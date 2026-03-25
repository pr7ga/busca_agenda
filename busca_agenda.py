import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Comparador de Telefones", layout="wide")

st.title("📱 Comparador de Telefones")
st.write("Compare números do Google Forms com sua agenda e identifique os que não estão salvos.")

# Função para normalizar telefone
def normalize_phone(phone):
    if pd.isna(phone):
        return None

    phone = str(phone)

    # Remove tudo que não for número
    phone = re.sub(r"\D", "", phone)

    # Remove zeros à esquerda (ex: 083...)
    phone = phone.lstrip("0")

    # Remove código do país (55) se existir
    if phone.startswith("55"):
        phone = phone[2:]

    # Agora garantimos que estamos comparando apenas DDD + número (11 dígitos)
    # Se tiver mais que 11, mantém os últimos 11
    if len(phone) > 11:
        phone = phone[-11:]

    # Se tiver menos de 10, provavelmente inválido
    if len(phone) < 10:
        return None

    return phone

# Upload dos arquivos
forms_file = st.file_uploader("📄 Upload CSV do Google Forms", type=["csv"])
contacts_file = st.file_uploader("📄 Upload CSV da Agenda", type=["csv"])

if forms_file and contacts_file:

    # Ler arquivos
    df_forms = pd.read_csv(forms_file)
    df_contacts = pd.read_csv(contacts_file)

    st.subheader("🔍 Pré-visualização")
    st.write("Google Forms:")
    st.dataframe(df_forms.head())

    st.write("Agenda:")
    st.dataframe(df_contacts.head())

    # Seleção das colunas
    forms_phone_col = st.selectbox("Selecione a coluna de telefone (Forms)", df_forms.columns)
    contacts_phone_col = st.selectbox("Selecione a coluna de telefone (Agenda)", df_contacts.columns)

    # Coluna opcional de indicativo (ex: prefixo, callsign, nome, etc.)
    forms_indicator_col = st.selectbox(
        "Selecione a coluna de indicativo (Forms) (opcional)",
        ["Nenhuma"] + list(df_forms.columns)
    )

    if st.button("🚀 Comparar"):

        # Normalizar telefones
        df_forms["telefone_norm"] = df_forms[forms_phone_col].apply(normalize_phone)
        df_contacts["telefone_norm"] = df_contacts[contacts_phone_col].apply(normalize_phone)

        # Conjunto de telefones da agenda
        contatos_set = set(df_contacts["telefone_norm"].dropna())

        # Filtrar os que NÃO estão na agenda
        df_nao_encontrados = df_forms[
            ~df_forms["telefone_norm"].isin(contatos_set)
        ].copy()

        # Resultado final
        if forms_indicator_col != "Nenhuma":
            resultado = df_nao_encontrados[[forms_indicator_col, forms_phone_col]]
            resultado.columns = ["Indicativo", "Telefone"]
        else:
            resultado = df_nao_encontrados[[forms_phone_col]]
            resultado.columns = ["Telefone"]

        st.subheader("📊 Resultado")
        st.write(f"Total não encontrados: {len(resultado)}")

        st.dataframe(resultado)

        # Download
        csv = resultado.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Baixar resultado em CSV",
            data=csv,
            file_name="numeros_nao_encontrados.csv",
            mime="text/csv"
        )
