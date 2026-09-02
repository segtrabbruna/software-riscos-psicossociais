import streamlit as st
from supabase import create_client


st.set_page_config(
    page_title="Gestão de Riscos Psicossociais",
    page_icon="🧠",
    layout="wide",
)


@st.cache_resource
def conectar_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])


supabase = conectar_supabase()


def entrar(email, senha):
    resposta = supabase.auth.sign_in_with_password({"email": email, "password": senha})
    st.session_state["sessao"] = resposta.session
    st.session_state["usuario"] = resposta.user


def sair():
    supabase.auth.sign_out()
    st.session_state.clear()
    st.rerun()


def pagina_login():
    st.title("Gestão de Riscos Psicossociais")
    st.write("Entre com o usuário administrador cadastrado no Supabase.")

    with st.form("form_login"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        enviar = st.form_submit_button("Entrar", use_container_width=True)

    if enviar:
        try:
            entrar(email.strip(), senha)
            st.rerun()
        except Exception:
            st.error("Não foi possível entrar. Confira o e-mail e a senha.")


def pagina_inicio():
    st.title("Painel geral")
    try:
        clientes = supabase.table("clientes").select("id", count="exact").execute()
        ghes = supabase.table("ghes").select("id", count="exact").execute()
        questionarios = supabase.table("questionarios").select("id", count="exact").execute()
        respostas = supabase.table("respostas").select("id", count="exact").eq("completa", True).execute()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Clientes", clientes.count or 0)
        col2.metric("GHEs", ghes.count or 0)
        col3.metric("Questionários", questionarios.count or 0)
        col4.metric("Respostas concluídas", respostas.count or 0)
    except Exception as erro:
        st.error(f"Não foi possível consultar o painel: {erro}")

    st.info("Esta é a primeira versão. Comece cadastrando um cliente e seus GHEs.")


def pagina_clientes():
    st.title("Clientes")

    with st.expander("Cadastrar novo cliente", expanded=True):
        with st.form("form_cliente", clear_on_submit=True):
            razao_social = st.text_input("Razão social *")
            nome_fantasia = st.text_input("Nome fantasia")
            cnpj = st.text_input("CNPJ")
            responsavel = st.text_input("Responsável")
            email = st.text_input("E-mail")
            salvar = st.form_submit_button("Salvar cliente")

        if salvar:
            if not razao_social.strip():
                st.warning("Informe a razão social.")
            else:
                dados = {
                    "razao_social": razao_social.strip(),
                    "nome_fantasia": nome_fantasia.strip() or None,
                    "cnpj": cnpj.strip() or None,
                    "responsavel": responsavel.strip() or None,
                    "email": email.strip() or None,
                }
                try:
                    supabase.table("clientes").insert(dados).execute()
                    st.success("Cliente cadastrado.")
                    st.rerun()
                except Exception as erro:
                    st.error(f"Não foi possível salvar: {erro}")

    try:
        resultado = (
            supabase.table("clientes")
            .select("id, razao_social, nome_fantasia, cnpj, responsavel, email, ativo")
            .order("razao_social")
            .execute()
        )
        if resultado.data:
            st.dataframe(resultado.data, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum cliente cadastrado.")
    except Exception as erro:
        st.error(f"Não foi possível listar os clientes: {erro}")


def pagina_ghes():
    st.title("GHEs")

    try:
        clientes = (
            supabase.table("clientes")
            .select("id, razao_social")
            .eq("ativo", True)
            .order("razao_social")
            .execute()
            .data
        )
    except Exception as erro:
        st.error(f"Não foi possível consultar os clientes: {erro}")
        return

    if not clientes:
        st.warning("Cadastre pelo menos um cliente antes de cadastrar um GHE.")
        return

    nomes_clientes = {item["razao_social"]: item["id"] for item in clientes}

    with st.expander("Cadastrar novo GHE", expanded=True):
        with st.form("form_ghe", clear_on_submit=True):
            cliente_nome = st.selectbox("Cliente *", list(nomes_clientes.keys()))
            codigo = st.text_input("Código do GHE *", placeholder="Ex.: GHE-01")
            nome = st.text_input("Nome do GHE *", placeholder="Ex.: Motoristas")
            descricao = st.text_area("Descrição")
            setor = st.text_input("Setor")
            cargos = st.text_input("Cargos")
            numero = st.number_input("Número de trabalhadores", min_value=0, step=1)
            salvar = st.form_submit_button("Salvar GHE")

        if salvar:
            if not codigo.strip() or not nome.strip():
                st.warning("Informe o código e o nome do GHE.")
            else:
                dados = {
                    "cliente_id": nomes_clientes[cliente_nome],
                    "codigo": codigo.strip(),
                    "nome": nome.strip(),
                    "descricao": descricao.strip() or None,
                    "setor": setor.strip() or None,
                    "cargos": cargos.strip() or None,
                    "numero_trabalhadores": int(numero),
                }
                try:
                    supabase.table("ghes").insert(dados).execute()
                    st.success("GHE cadastrado.")
                    st.rerun()
                except Exception as erro:
                    st.error(f"Não foi possível salvar: {erro}")

    try:
        resultado = (
            supabase.table("ghes")
            .select("codigo, nome, setor, cargos, numero_trabalhadores, ativo, clientes(razao_social)")
            .order("nome")
            .execute()
        )
        if resultado.data:
            linhas = []
            for item in resultado.data:
                linhas.append(
                    {
                        "Cliente": (item.get("clientes") or {}).get("razao_social", ""),
                        "Código": item.get("codigo"),
                        "GHE": item.get("nome"),
                        "Setor": item.get("setor"),
                        "Cargos": item.get("cargos"),
                        "Trabalhadores": item.get("numero_trabalhadores"),
                        "Ativo": item.get("ativo"),
                    }
                )
            st.dataframe(linhas, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum GHE cadastrado.")
    except Exception as erro:
        st.error(f"Não foi possível listar os GHEs: {erro}")


if "sessao" not in st.session_state:
    pagina_login()
    st.stop()

with st.sidebar:
    st.header("Riscos Psicossociais")
    pagina = st.radio("Menu", ["Início", "Clientes", "GHEs"])
    st.divider()
    if st.button("Sair", use_container_width=True):
        sair()

if pagina == "Início":
    pagina_inicio()
elif pagina == "Clientes":
    pagina_clientes()
else:
    pagina_ghes()
