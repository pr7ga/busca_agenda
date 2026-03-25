import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Comparador de Telefones", layout="wide")

st.title("📱 Comparador de Telefones (robusto)")
st.write("Comparação baseada no núcleo do número (evita erros com 9º dígito).")

# =========================
# 🔧 LIMPEZA BÁSICA
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


# =========================
# 🧠 EXTRAI NÚCLEO (últimos 8 dígitos)
# =========================
def extrair_nucleo(numero):
    if not numero:
        return None

    return numero[-8:]  # ESSA É A CHAVE!


# =========================
# 📂 UPLOAD
# =========================
forms_file = st.file_uploader("📄 CSV do Google Forms", type=["csv"])
contacts_file = st.file_uploader("📄 CSV da Agenda", type=["csv"])

if forms_file and contacts_file:

    df_forms = pd.read_csv(forms_file)
    df_contacts = pd.read_csv(contacts_file)

    st.subheader("🔍 Pré-visualização")
    st.dataframe(df_forms.head())
    st.dataframe(df_contacts.head())

    # Seleção de colunas
    forms_phone_col = st.selectbox("Telefone (Forms)", df_forms.columns)
    contacts_phone_col = st.selectbox("Telefone (Agenda)", df_contacts.columns)

    forms_indicator_col = st.selectbox(
        "Indicativo (opcional)",
        ["Nenhuma"] + list(df_forms.columns)
    )

    if st.button("🚀 Comparar"):

        # =========================
        # 🔄 LIMPAR
        # =========================
        df_forms["numero_limpo"] = df_forms[forms_phone_col].apply(limpar_numero)
        df_contacts["numero_limpo"] = df_contacts[contacts_phone_col].apply(limpar_numero)

        # =========================
        # 🧠 NÚCLEO
        # =========================
        df_forms["nucleo"] = df_forms["numero_limpo"].apply(extrair_nucleo)
        df_contacts["nucleo"] = df_contacts["numero_limpo"].apply(extrair_nucleo)

        # Conjunto da agenda
        nucleos_agenda = set(df_contacts["nucleo"].dropna())

        # =========================
        # 🔍 DIAGNÓSTICO INTELIGENTE
        # =========================
        def diagnostico(row):
            original = row[forms_phone_col]
            numero = row["numero_limpo"]
            nucleo = row["nucleo"]

            if pd.isna(original) or original == "":
                return "Telefone vazio"

            if not numero:
                return "Número inválido"

            if not nucleo:
                return "Número muito curto"

            if nucleo in nucleos_agenda:
                # Agora detecta diferenças
                if len(numero) == 11:
                    return "OK (bate pelo núcleo - com 9)"
                elif len(numero) == 10:
                    return "OK (bate pelo núcleo - sem 9)"
                else:
                    return "OK (bate pelo núcleo)"

            # Não bateu → tentar explicar

            # mesmo número com possível DDD diferente
            for n in df_contacts["numero_limpo"].dropna():
                if numero[-8:] == n[-8:]:
                    return "Mesmo número, DDD diferente"

            if len(numero) == 11:
                return "Não encontrado (pode estar sem 9)"

            if len(numero) == 10:
                return "Não encontrado (pode estar com 9)"

            return "Não encontrado"

        df_forms["diagnostico"] = df_forms.apply(diagnostico, axis=1)

        df_nao_encontrados = df_forms[
            ~df_forms["diagnostico"].str.startswith("OK")
        ].copy()

        # =========================
        # 📊 RESULTADO
        # =========================
        st.subheader("📊 Resultado")

        if forms_indicator_col != "Nenhuma":
            resultado = df_nao_encontrados[
                [forms_indicator_col, forms_phone_col, "diagnostico"]
            ]
            resultado.columns = ["Indicativo", "Telefone", "Diagnóstico"]
        else:
            resultado = df_nao_encontrados[
                [forms_phone_col, "diagnostico"]
            ]
            resultado.columns = ["Telefone", "Diagnóstico"]

        st.write(f"Total não encontrados: {len(resultado)}")
        st.dataframe(resultado)

        # Download
        csv = resultado.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇️ Baixar CSV",
            csv,
            "resultado.csv",
            "text/csv"
        )

        # Debug opcional
        with st.expander("🔎 Debug"):
            st.dataframe(df_forms[[forms_phone_col, "numero_limpo", "nucleo", "diagnostico"]])
