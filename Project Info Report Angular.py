import os
import re
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import grey

def get_project_structure(start_path):
    structure = []
    for root, dirs, files in os.walk(start_path):
        level = root.replace(start_path, '').count(os.sep)
        indent = '  ' * level
        structure.append(f"{indent}{os.path.basename(root)}/")
        subindent = '  ' * (level + 1)
        for f in files:
            if f.endswith(('.html', '.ts', '.scss')):
                structure.append(f"{subindent}{f}")
    return '\n'.join(structure)

def read_file_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def find_imports(content, file_type):
    imports = []
    if file_type == '.scss':
        # Match @import statements in SCSS
        imports = re.findall(r'@import\s+[\'"]([^\'"]+)[\'"]', content)
    elif file_type == '.ts':
        # Match import statements in TypeScript
        imports = re.findall(r'import.*?from\s+[\'"]([^\'"]+)[\'"]', content)
    return imports

def resolve_import_path(import_path, file_path, project_path):
    if import_path.startswith('~'):
        # This is likely a node_modules import
        return os.path.join(project_path, 'node_modules', import_path[1:])
    else:
        # This is likely a relative import
        return os.path.join(os.path.dirname(file_path), import_path)

def gather_project_info(project_path):
    project_info = {
        'structure': get_project_structure(project_path),
        'files': {}
    }

    for root, _, files in os.walk(project_path):
        for file in files:
            if file.endswith(('.html', '.ts', '.scss')):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, project_path)
                content = read_file_content(file_path)
                project_info['files'][relative_path] = content

                # Find and include imports
                file_type = os.path.splitext(file)[1]
                imports = find_imports(content, file_type)
                for imp in imports:
                    import_path = resolve_import_path(imp, file_path, project_path)
                    if os.path.exists(import_path):
                        import_relative_path = os.path.relpath(import_path, project_path)
                        if import_relative_path not in project_info['files']:
                            project_info['files'][import_relative_path] = read_file_content(import_path)

    return project_info

def save_project_info_pdf(project_info, output_file):
    doc = SimpleDocTemplate(output_file, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("Project Information", styles['Title']))
    story.append(Spacer(1, 12))

    # Project Structure
    story.append(Paragraph("Project Structure", styles['Heading1']))
    story.append(Spacer(1, 12))
    story.append(Preformatted(project_info['structure'], styles['Code']))
    story.append(Spacer(1, 12))

    # File Contents
    story.append(Paragraph("File Contents", styles['Heading1']))
    story.append(Spacer(1, 12))

    code_style = ParagraphStyle(
        'Code',
        parent=styles['BodyText'],
        fontName='Courier',
        fontSize=8,
        leading=10,
        leftIndent=20,
        rightIndent=20,
        backColor=grey,
        spaceAfter=10
    )

    for file_path, content in project_info['files'].items():
        story.append(Paragraph(file_path, styles['Heading2']))
        story.append(Spacer(1, 6))
        story.append(Preformatted(content, code_style))
        story.append(Spacer(1, 12))

    doc.build(story)

if __name__ == "__main__":
    project_path = input("Enter the path to your project: ")
    output_file = input("Enter the name of the output file (e.g., project_info.pdf): ")
    
    project_info = gather_project_info(project_path)
    save_project_info_pdf(project_info, output_file)
    
    print(f"Project information has been saved to {output_file}")
