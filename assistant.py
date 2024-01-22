from langchain_community.document_loaders import UnstructuredPDFLoader


loader = UnstructuredPDFLoader("data/flinthill/middle-school/FHS_MS_O&M Documents.pdf")


data = loader.load()
