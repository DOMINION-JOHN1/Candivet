
!pip install langchain
!pip install langchain_community
!pip install --upgrade langchain-core
!pip install pypdf
!pip install PyPDF2

from flask import Flask, request, jsonify
import google.generativeai as genai
from langchain.document_loaders import PyPDFLoader
from langchain.prompts import PromptTemplate

app = Flask(__name__)


#save uploaded file and return path
def save_uploaded_file(uploaded_file):
    # Create a temporary directory
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# Function to load and extract content from a PDF using PyPDFLoader
def load_pdf_content(pdf_file):
    content = []
    try:
        pdf_loader = PyPDFLoader(pdf_file)
        pdf_documents = pdf_loader.load()
        content.extend(pdf_documents)  # Add the entire list of documents to the content list
    except Exception as e:
        print(f"Failed to load PDF from {pdf_file.filename}: {e}")
    return content

@app.route('/upload_job_description', methods=['POST'])
def upload_job_description():
    # Retrieve job description from the request
    job_description_file = request.files['job_description']
    job_description_path = save_uploaded_file(job_description_file)
    
    # Extract content from the job description file
    job_description_loader = PyPDFLoader(job_description_path)
    job_description = job_description_loader.load()
    
    # Save the job description content to a global variable or database
    global job_description_content
    job_description_content = "\n".join([doc.page_content for doc in job_description])
    
    return jsonify({'message': 'Job description uploaded successfully'}), 200

@app.route('/process_cvs', methods=['POST'])
def process_cvs():
    # Ensure that the job description has been uploaded
    if 'job_description_content' not in globals():
        return jsonify({'error': 'Job description not uploaded'}), 400

    # Retrieve CVs from the request
    cv_files = request.files.getlist('cvs')
    
    # Extract content from the CV files
    pages_content = []
    for cv_file in cv_files[:5]:  # Limit to any 5 CVs
        separator = f"\n{'='*40}\nContent from: {cv_file.filename}\n{'='*40}\n"
        pages_content.append(separator)  # Add a separator for each CV

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
    
    # Use the Generative AI model
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(formatted_prompt)
    
    return jsonify({'ranked_cvs': response.text})

if __name__ == '__main__':
    app.run(debug=True)








