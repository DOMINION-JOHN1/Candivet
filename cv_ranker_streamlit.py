import streamlit as st
import google.generativeai as genai
from langchain.document_loaders import PyPDFLoader
from langchain.prompts import PromptTemplate


GEMINI_API_KEY= st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

# Function to load and extract content from a PDF using PyPDFLoader
def load_pdf_content(pdf_file):
    content = []
    try:
        pdf_loader = PyPDFLoader(pdf_file)
        pdf_documents = pdf_loader.load()
        content.extend(pdf_documents)  # Add the entire list of documents to the content list
    except Exception as e:
        st.error(f"Failed to load PDF from {pdf_file.name}: {e}")
    return content


def save_uploaded_file(uploaded_file):
    # Create a temporary directory
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path


# Streamlit app
def main():
    st.title("CV Ranking and Summarization App")

    # Step 1: Upload Job Description
    st.header("Upload Job Description")
    job_description_file = st.file_uploader("Choose a Job Description PDF", type="pdf")
    
    if job_description_file:

        # Save the uploaded file and get the file path
        job_description_path = save_uploaded_file(job_description_file)
        # Extract content from the job description file
        job_description_loader = PyPDFLoader(job_description_path)
        job_description = job_description_loader.load()
        job_description_content = "\n".join([doc.page_content for doc in job_description])
        st.success("Job description uploaded successfully!")
    else:
        st.warning("Please upload a job description file.")
        job_description_content = None

    # Step 2: Upload CVs
    st.header("Upload CVs")
    cv_files = st.file_uploader("Choose CV PDFs", type="pdf", accept_multiple_files=True)
    
    if cv_files and job_description_content:
        # Extract content from the CV files
        pages_content = []
        for cv_file in cv_files[:5]:  # Limit to any 5 CVs
            separator = f"\n{'='*40}\nContent from: {cv_file.name}\n{'='*40}\n"
            pages_content.append(separator)  # Add a separator for each CV
            # Save the uploaded file and get the file path
            cv_file_path = save_uploaded_file(cv_file)
            pdf_content = load_pdf_content(cv_file_path)
            
            for document in pdf_content:
                pages_content.append(document.page_content)
            
            pages_content.append("\n")  # Add a new line after each CV's content
        
        CVs = "\n".join(pages_content)

        # Create the prompt
        template = """
        You are a recruitment manager tasked to rank the CVs by their relevance to the job description. You are to generate concise, two-paragraph summaries for all the CVs. These summaries should emphasize the key skills, experiences, and qualifications that are most relevant to the given job description in the Context:
        Ensure you do not make any other suggestions.
        Context: {context}

        Question: {question}
        """
        
        prompt = PromptTemplate.from_template(template)
        formatted_prompt = prompt.format(
            context=job_description_content,
            question="Rank the CVs by their relevance to the job description in the Context. Generate a concise, two-paragraph summaries for all these CVs. The summaries should emphasize the key skills, experiences, and qualifications that are most relevant to the given job description in the Context" + str(CVs)
        )
        
        # Generate content using the Generative AI model
        if st.button("Process CVs"):
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(formatted_prompt)
            st.header("Ranked CVs and Summaries")
            st.text(response.text)
    elif not job_description_content:
        st.warning("Please upload the job description before processing CVs.")

if __name__ == "__main__":
    main()
