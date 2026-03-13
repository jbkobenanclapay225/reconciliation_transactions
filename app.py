import streamlit as st
import pandas as pd
from io import BytesIO

st.title("Réconciliation Transactions")

# Upload multiple fichiers pour chaque source
files_transactions = st.file_uploader(
    "Fichiers Marchand",
    type="csv",
    accept_multiple_files=True
)

files_payments = st.file_uploader(
    "Données CLAPAY Marchand",
    type="csv",
    accept_multiple_files=True
)
run = st.button("Lancer la réconciliation")

# Fonction pour concaténer les fichiers d'un input
def load_and_concat(files, sep=None):
    dfs = []
    for f in files:
        df = pd.read_csv(f, encoding="utf-8", engine="python", delimiter=sep)
        df.columns = df.columns.str.strip()
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


if run:

    if not files_transactions or not files_payments:
        st.warning("Veuillez importer les deux types de fichiers SVP!!")
        st.stop()
    # concaténation des fichiers
    transaction_all = load_and_concat(files_transactions, sep=";")
    payment_feb = load_and_concat(files_payments, sep=";")

    # Conversion types
    def clean_numeric(df, col):
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(',', '.', regex=False)
                .str.replace(' ', '', regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Colonnes plateforme
    clean_numeric(transaction_all, "Fee")
    clean_numeric(transaction_all, "Amount")

    # Colonnes marchand
    clean_numeric(payment_feb, "fee_value")
    clean_numeric(payment_feb, "amount")

        

    st.subheader("Aperçu Plateforme")
    st.dataframe(transaction_all.head())

    st.subheader("Aperçu Marchand")
    st.dataframe(payment_feb.head())
    
    # Merge pour détecter transactions manquantes
    diff = payment_feb.merge(
        transaction_all,
        left_on="transaction_id",
        right_on="UUID",
        how="outer",
        indicator=True
    )
    
    # Totaux
    total_marchand = payment_feb.groupby("method")["amount"].sum()
    total_plateforme = transaction_all.groupby("Type")["Amount"].sum()

    
    fee_plateforme = transaction_all["Fee"].sum()
    fee_marchand = payment_feb["fee_value"].sum()

    # Vérification
    verification = {

        "deposit": {
            "marchand": total_marchand.get("MERCHANT", 0),
            "plateforme": total_plateforme.get("deposit", 0),
            "ecart": total_marchand.get("MERCHANT", 0) - total_plateforme.get("deposit", 0)
        },

        "withdrawal": {
            "marchand": total_marchand.get("CASHIN", 0),
            "plateforme": total_plateforme.get("withdraw", 0),
            "ecart": total_marchand.get("CASHIN", 0) - total_plateforme.get("withdraw", 0)
        },

        "fees": {
            "marchand": fee_marchand,
            "plateforme": fee_plateforme,
            "ecart": fee_marchand - fee_plateforme
        }
    }

    Ecart_Totaux = pd.DataFrame(verification)

    st.subheader("Ecarts Totaux")
    st.dataframe(Ecart_Totaux)

    # distinguer les lignes « manquantes » des véritables divergences de valeurs
    only_in_merchant  = diff[diff["_merge"] == "left_only"]  
    only_in_platform  = diff[diff["_merge"] == "right_only"]  

    matched = diff[diff["_merge"] == "both"]

    amount_mismatch = matched["amount"].fillna(-1)    != matched["Amount"].fillna(-2)
    fee_mismatch    = matched["fee_value"].fillna(-1) != matched["Fee"].fillna(-2)
    status_merchant = matched["status"].fillna("").str.upper() != "SUCCESSFUL"
    status_platform = matched["Status"].fillna("").str.lower() != "succeeded"

    erreur = matched[amount_mismatch | fee_mismatch | status_merchant | status_platform]

    st.subheader("Transactions manquantes (Marchand uniquement)")
    st.dataframe(only_in_merchant)

    st.subheader("Transactions manquantes (Plateforme uniquement)")
    st.dataframe(only_in_platform)

    st.subheader("Erreurs détectées (présentes des deux côtés, valeurs différentes)")
    st.dataframe(erreur)

    # And include all three sheets in the Excel export
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        Ecart_Totaux.to_excel(writer,        sheet_name="Ecart Totaux",         index=True)
        erreur.to_excel(writer,              sheet_name="Erreurs valeurs",       index=False)
        only_in_merchant.to_excel(writer,    sheet_name="Manquants Marchand",    index=False)
        only_in_platform.to_excel(writer,    sheet_name="Manquants Plateforme",  index=False)
    output.seek(0)

    st.download_button(
        label="Télécharger le rapport Excel",
        data=output,
        file_name="Reconciliations.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )