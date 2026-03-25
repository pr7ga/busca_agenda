import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Comparador de Contatos", layout="wide")

st.title("📱📡 Comparador de Contatos")
st.write("Compare contatos por telefone ou indicativo (extraído automaticamente da agenda).")

# =========================
# 📱 TELEFONE
# =========================
def limpar_numero(phone):
    if pd.isna(phone):
        return None

    phone = str(phone)
    phone = re.sub(r"\D", "", phone)

    if phone.startswith("55"):
        phone = phone[2:]

    phone = phone.lstrip("0")

    if len(phone) < 8:
        return None

    return phone


def extrair_nucleo(numero):
    if not numero:
        return None
    return numero[-8:]


# =========================
# 📡 INDICATIVO
# =========================
REGEX_INDICATIVO = re.compile(r"\b(PP|PU|PY|PR|PS|ZX|ZZ)[0-9][A-Z]{2,3}\b")

def extrair_indicativos(texto):
    if pd.isna(texto):
        return []

    texto = str(texto).upper()

    return [m.group(0) for m in REGEX_INDICATIVO.finditer(texto)]


# =========================
# 📂 UPLOAD
# =========================
forms_file = st.file_uploader("📄 CSV do Google Forms", type=["csv"])
contacts_file = st.file_uploader("📄 CSV da Agenda", type=["csv"])

if forms_file and contacts_file:

    df_forms = pd.read_csv(forms_file)
    df_contacts = pd.read_csv(contacts_file)

    st.subheader("🔍 Pré-visualização")
    st.write("Forms:")
    st.dataframe(df_forms.head())

    st.write("Agenda:")
    st.dataframe(df_contacts.head())

    # =========================
    # 🎯 MODO
    # =========================
    modo = st.radio("Modo de comparação:", ["Telefone", "Indicativo"])

    # =========================
    # 📱 TELEFONE
    # =========================
    if modo == "Telefone":

        forms_phone_col = st.selectbox("Telefone (Forms)", df_forms.columns)
        contacts_phone_col = st.selectbox("Telefone (Agenda)", df_contacts.columns)

        if st.button("🚀 Comparar"):

            df_forms["numero_limpo"] = df_forms[forms_phone_col].apply(limpar_numero)
            df_contacts["numero_limpo"] = df_contacts[contacts_phone_col].apply(limpar_numero)

            df_forms["nucleo"] = df_forms["numero_limpo"].apply(extrair_nucleo)
            df_contacts["nucleo"] = df_contacts["numero_limpo"].apply(extrair_nucleo)

            nucleos_agenda = set(df_contacts["nucleo"].dropna())

            def diagnostico(row):
                numero = row["numero_limpo"]
                nucleo = row["nucleo"]

                if not numero:
                    return "Número inválido"

                if nucleo in nucleos_agenda:
                    return "OK"

                return "Não encontrado"

            df_forms["diagnostico"] = df_forms.apply(diagnostico, axis=1)

            resultado = df_forms[df_forms["diagnostico"] != "OK"][
                [forms_phone_col, "diagnostico"]
            ]

            resultado.columns = ["Telefone", "Diagnóstico"]

            st.write(f"Total não encontrados: {len(resultado)}")
            st.dataframe(resultado)

            csv = resultado.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Baixar CSV", csv, "resultado_telefone.csv", "text/csv")

    # =========================
    # 📡 INDICATIVO
    # =========================
    else:

        forms_indicativo_col = st.selectbox("Indicativo (Forms)", df_forms.columns)
        forms_phone_col = st.selectbox("Telefone (Forms)", df_forms.columns)

        if st.button("🚀 Comparar"):

            # Forms
            df_forms["indicativo"] = (
                df_forms[forms_indicativo_col]
                .astype(str)
                .str.upper()
                .str.strip()
            )

            # Agenda → concatena campos
            df_contacts["texto"] = (
                df_contacts["First Name"].fillna("") + " " +
                df_contacts["Middle Name"].fillna("") + " " +
                df_contacts["Last Name"].fillna("")
            )

            # Extrair indicativos da agenda
            df_contacts["indicativos_extraidos"] = df_contacts["texto"].apply(extrair_indicativos)

            # Criar conjunto único
            indicativos_agenda = set()
            for lista in df_contacts["indicativos_extraidos"]:
                indicativos_agenda.update(lista)

            # Diagnóstico
            def diagnostico(ind):
                if not ind or ind == "NAN":
                    return "Indicativo vazio"

                if ind in indicativos_agenda:
                    return "OK"

                if re.match(r".*[0-9].*", ind) is None:
                    return "Formato inválido"

                return "Não encontrado na agenda"

            df_forms["diagnostico"] = df_forms["indicativo"].apply(diagnostico)

            resultado = df_forms[df_forms["diagnostico"] != "OK"][
                [forms_indicativo_col, forms_phone_col, "diagnostico"]
            ]

            resultado.columns = ["Indicativo", "Telefone", "Diagnóstico"]

            st.write(f"Total não encontrados: {len(resultado)}")
            st.dataframe(resultado)

            csv = resultado.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Baixar CSV", csv, "resultado_indicativos.csv", "text/csv")

            # Debug opcional
            with st.expander("🔎 Indicativos extraídos da agenda"):
                st.write(sorted(indicativos_agenda))
