import streamlit as st
import zipfile
import os
import xml.etree.ElementTree as ET
from docx import Document

def parse_word_questions(filepath):
    """Parse les questions formatées depuis un fichier Word."""
    doc = Document(filepath)
    questions = []
    current_question = None
    
    for para in doc.paragraphs:
        text = para.text.strip()
        if text and text[0].isdigit() and text[1] == ".":
            if current_question:
                questions.append(current_question)
            current_question = [text[2:].strip(), []]
        elif text and current_question and text[0].lower() in "abcde" and text[1] == ".":
            correct = text.endswith("*")
            answer_text = text[2:].strip(" *")  # Supprime la lettre, le point et l'astérisque éventuelle
            current_question[1].append((answer_text, correct))
    
    if current_question:
        questions.append(current_question)
    
    return questions

def generate_qti_zip_per_question(questions):
    """Génère un fichier ZIP par question contenant question.xml."""
    zip_files = []
    
    for index, (question_text, answers) in enumerate(questions, start=1):
        question_id = f"MULTIPLECHOICE_QUESTION_{index:06d}"
        title = st.text_input(f"Entrez le titre pour la question {index}", question_text[:50])
        
        question_root = ET.Element("assessmentItem", {
            "xmlns": "http://www.imsglobal.org/xsd/imsqti_v2p1",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "identifier": question_id,
            "title": title,
            "timeDependent": "false",
            "adaptive": "false"
        })
        
        response_declaration = ET.SubElement(question_root, "responseDeclaration", {
            "identifier": "RESPONSE",
            "cardinality": "multiple",
            "baseType": "identifier"
        })
        correct_response = ET.SubElement(response_declaration, "correctResponse")
        
        item_body = ET.SubElement(question_root, "itemBody")
        choice_interaction = ET.SubElement(item_body, "choiceInteraction", {
            "responseIdentifier": question_id,
            "maxChoices": str(len(answers))
        })
        
        prompt = ET.SubElement(choice_interaction, "prompt")
        prompt.text = question_text
        
        for i, (answer_text, correct) in enumerate(answers, start=1):
            choice_id = f"CHOICE_{index:06d}_{i}"
            if correct:
                ET.SubElement(correct_response, "value").text = choice_id
            simple_choice = ET.SubElement(choice_interaction, "simpleChoice", {"identifier": choice_id})
            simple_choice.text = answer_text
        
        question_xml_path = f"question_{index:06d}.xml"
        ET.ElementTree(question_root).write(question_xml_path, encoding="utf-8", xml_declaration=True)
        
        # Création du package ZIP par question
        zip_filename = f"qti_package_{index:06d}.zip"
        with zipfile.ZipFile(zip_filename, 'w') as qti_zip:
            qti_zip.write(question_xml_path, "question.xml")
        zip_files.append(zip_filename)
    
    return zip_files

def main():
    st.title("Générateur de fichiers QTI à partir de Word")
    uploaded_file = st.file_uploader("Téléversez un fichier Word", type=["docx"])
    
    if uploaded_file:
        with open("temp.docx", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        questions = parse_word_questions("temp.docx")
        
        if not questions:
            st.error("Aucune question trouvée dans le fichier Word.")
            return
        
        zip_files = generate_qti_zip_per_question(questions)
        
        for zip_file in zip_files:
            with open(zip_file, "rb") as f:
                st.download_button(label=f"Télécharger {zip_file}", data=f, file_name=zip_file)

if __name__ == "__main__":
    main()
