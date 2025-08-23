import streamlit as st
import fitz  # PyMuPDF for PDF handling
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI

# Ensure you have set your OpenAI API key in the Streamlit secrets
# You can set it in the Streamlit Cloud or in a .streamlit/secrets.toml file
api_key = st.secrets["OPENAI_API_KEY"]

# Pinecone setup
PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
INDEX_NAME = "developer-quickstart-py"

# Create Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)

# Create index if not exists
if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=INDEX_NAME,
        dimension=1536,  # for text-embedding-3-small
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )


index = pc.Index(INDEX_NAME)

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
if uploaded_file:
    # Read PDF and extract text
    knowledge_base = ""
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        for page in doc:
            knowledge_base += page.get_text()

    st.subheader("Extracted Text Preview")
    st.write(knowledge_base[:1000] + "...")  # Show first 1000 chars

    def fixed_word_chunk(text, chunk_size=20):
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size])
            chunks.append(chunk)
        return chunks

    knowledge_chunks = fixed_word_chunk(knowledge_base, chunk_size=20)
    st.write(f"Total chunks: {len(knowledge_chunks)}")

    client = OpenAI(api_key=api_key)

    def get_embedding(text):
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

    # Add chunks to Pinecone
    if st.button("Process and Store Chunks"):
        with st.spinner("Embedding and storing chunks..."):
            vectors = []
            for i, chunk in enumerate(knowledge_chunks):
                embedding = get_embedding(chunk)
                vectors.append((
                    f"chunk-{i+1}",
                    embedding,
                    {"text": chunk}
                ))
            index.upsert(vectors)
        st.success("Chunks processed and stored!")

    query = st.text_input("Enter your query")
    if query and st.button("Ask"):
        query_embedding = get_embedding(query)
        # Query Pinecone for top 2 matches
        results = index.query(
            vector=query_embedding,
            top_k=2,
            include_metadata=True
        )
        top_chunks = [match['metadata']['text'] for match in results['matches']]
        top_chunks_str = ", ".join(top_chunks)

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "user",
                "content": f"You are a very good writer, who writes very good documents. Given {top_chunks_str} and {query}, give me a good answer, keep human touch."
            }]
        )
        st.subheader("RAG Response")
        st.write(response.choices[0].message.content)