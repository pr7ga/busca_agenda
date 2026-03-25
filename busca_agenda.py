import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Comparador de Telefones", layout="wide")

st.title("📱 Comparador de Telefones")
st.write("Compare números do Google Forms com sua agenda e identifique os que não estão salvos.")

# =========================
# 🔧 NORMALIZAÇÃO
# =========================
def normalize_phone(phone):
    if pd.isna(phone):
        return None

    phone = str(phone)
    phone = re.sub(r"\D", "", phone)

    phone = phone.lstrip("0")

    if phone.startswith("55"):
        phone = phone[2:]

    if len(phone) > 11:
        phone = phone[-11:]

    if len(phone) < 10:
        return None

    return phone


# =========================
# 🔁 GERAR VARIANTES
# =========================
def gerar_variantes(numero):
    variantes = set()

    if not numero:
        return variantes

    variantes.add(numero)

    # Com 9 → sem 9
    if len(numero) == 11:
        ddd = numero[:2]
        restante = numero[2:]

        if restante.startswith("9"):
            variantes.add(ddd + restante[1:])

    # Sem 9 → com 9
    if len(numero) == 10:
        ddd = numero[:2]
        restante = numero[2:]

        variantes.add(ddd + "9" + restante)

    return variantes


# =========================
# 📂 UPLOAD
# =========================
forms_file = st.file_uploader("📄 Upload CSV do Google Forms", type=["csv"])
contacts_file = st.file_uploader("📄 Upload CSV da Agenda", type=["csv"])

if forms_file and contacts_file:

    df_forms = pd.read_csv(forms_file)
    df_contacts = pd.read_csv(contacts_file)

    st.subheader("🔍 Pré-visualização")
    st.write("Google Forms:")
    st.dataframe(df_forms.head())

    st.write("Agenda:")
    st.dataframe(df_contacts.head())

    # =========================
    # 🎯 SELEÇÃO DE COLUNAS
    # =========================
    forms_phone_col = st.selectbox("Telefone (Forms)", df_forms.columns)
    contacts_phone_col = st.selectbox("Telefone (Agenda)", df_contacts.columns)

    forms_indicator_col = st.selectbox(
        "Indicativo (Forms) (opcional)",
        ["Nenhuma"] + list(df_forms.columns)
    )

    if st.button("🚀 Comparar"):

        # =========================
        # 🔄 NORMALIZAR
        # =========================
        df_forms["telefone_norm"] = df_forms[forms_phone_col].apply(normalize_phone)
        df_contacts["telefone_norm"] = df_contacts[contacts_phone_col].apply(normalize_phone)

        # =========================
        # 📚 BASE DA AGENDA
        # =========================
        contatos_set = set()
        contatos_originais = {}

        for num in df_contacts["telefone_norm"].dropna():
            variantes = gerar_variantes(num)
            for v in variantes:
                contatos_set.add(v)
                contatos_originais[v] = num  # guarda origem

        # =========================
        # 🔍 DIAGNÓSTICO
        # =========================
        def diagnostico(numero_original, numero_norm):
            if not numero_original or pd.isna(numero_original):
                return "Telefone vazio"

            if not numero_norm:
                return "Número inválido após normalização"

            variantes = gerar_variantes(numero_norm)

            # Match direto
            for v in variantes:
                if v in contatos_set:
                    original = contatos_originais.get(v, "")
                    if numero_norm == original:
                        return "OK (encontrado)"
                    else:
                        return "OK (equivalente com/sem 9)"

            # Diagnósticos detalhados
            if len(numero_norm) < 10:
                return "Número incompleto"

            if len(numero_norm) > 11:
                return "Número com dígitos excedentes"

            # Possível DDD diferente
            for contato in contatos_set:
                if numero_norm[-8:] == contato[-8:]:
                    return "Mesmo número, DDD diferente"

            # Possível sem 9
            if len(numero_norm) == 11 and numero_norm[2] == "9":
                return "Pode estar sem o 9 na agenda"

            if len(numero_norm) == 10:
                return "Pode estar com 9 adicional na agenda"

            return "Não encontrado na agenda"

        # =========================
        # 🚀 PROCESSAMENTO
        # =========================
        df_forms["diagnostico"] = df_forms.apply(
            lambda row: diagnostico(row[forms_phone_col], row["telefone_norm"]),
            axis=1
        )

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

        # =========================
        # 📥 DOWNLOAD
        # =========================
        csv = resultado.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="⬇️ Baixar resultado em CSV",
            data=csv,
            file_name="numeros_nao_encontrados_com_diagnostico.csv",
            mime="text/csv"
        )

        # =========================
        # 🔎 DEBUG OPCIONAL
        # =========================
        with st.expander("🔎 Ver telefones normalizados"):
            st.write("Forms:")
            st.dataframe(df_forms[[forms_phone_col, "telefone_norm", "diagnostico"]])

            st.write("Agenda:")
            st.dataframe(df_contacts[[contacts_phone_col, "telefone_norm"]])
