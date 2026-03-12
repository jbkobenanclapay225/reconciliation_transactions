import streamlit as st
import pandas as pd
from io import BytesIO

st.title("Réconciliation Transactions")

# Upload multiple fichiers pour chaque source
files_transactions = st.file_uploader(
    "Fichiers Plateforme (transactions-all ...)",
    type="csv",
    accept_multiple_files=True
)

files_payments = st.file_uploader(
    "Fichiers Marchand (payment ...)",
    type="csv",
    accept_multiple_files=True
)
run = st.button("Lancer la réconciliation")

# Fonction pour concaténer les fichiers d'un input
def load_and_concat(files, sep=None):
    dfs = []
    for f in files:
        df = pd.read_csv(f, encoding="utf-8", engine="python", delimiter=sep)
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


if run:

    if not files_transactions or not files_payments:
        st.warning("Veuillez importer les deux types de fichiers SVP!!")
        st.stop()
    # concaténation des fichiers
    transaction_all = load_and_concat(files_transactions, sep=";")
    payment_feb = load_and_concat(files_payments, sep=";")

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

    # Conversion types
    diff["amount"] = pd.to_numeric(diff["amount"], errors="coerce")
    diff["Amount"] = pd.to_numeric(diff["Amount"], errors="coerce")
    diff["Fee"] = pd.to_numeric(diff["Fee"], errors="coerce")
    diff["fee_value"] = pd.to_numeric(diff["fee_value"], errors="coerce")

    # Détection erreurs
    erreur = diff[
        (diff["amount"] != diff["Amount"]) |
        (diff["fee_value"] != diff["Fee"]) |
        (diff["status"] != "SUCCESSFUL") |
        (diff["Status"] != "succeeded")
    ]

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

    st.subheader("Erreurs détectées")
    st.dataframe(erreur)

    # Export Excel en mémoire
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        Ecart_Totaux.to_excel(writer, sheet_name="Ecart Totaux", index=True)
        erreur.to_excel(writer, sheet_name="Erreurs", index=False)

    output.seek(0)

    st.download_button(
        label="Télécharger le rapport Excel",
        data=output,
        file_name="Reconciliations.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
