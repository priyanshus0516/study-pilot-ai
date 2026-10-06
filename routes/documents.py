import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from werkzeug.utils import secure_filename
from database.database import db
from database.models import Document, DocumentChunk, StudyActivity
from routes.auth import login_required, get_current_user
from services.document_processor import DocumentProcessor

documents_bp = Blueprint('documents', __name__, url_prefix='/documents')

@documents_bp.route('/', methods=['GET'])
@login_required
def list_documents():
    user = get_current_user()
    docs = Document.query.filter_by(user_id=user.id).order_by(Document.uploaded_at.desc()).all()
    return render_template('upload.html', documents=docs)

@documents_bp.route('/upload', methods=['POST'])
@login_required
def upload_document():
    user = get_current_user()

    if 'file' not in request.files:
        flash('No file part provided in the upload request.', 'danger')
        return redirect(url_for('documents.list_documents'))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected. Please choose a PDF, TXT, or DOCX document.', 'warning')
        return redirect(url_for('documents.list_documents'))

    if not DocumentProcessor.allowed_file(file.filename):
        flash('Unsupported file type. Please upload a PDF, TXT, or DOCX file.', 'danger')
        return redirect(url_for('documents.list_documents'))

    original_name = file.filename
    clean_name = secure_filename(original_name)
    if not clean_name:
        clean_name = f"doc_{int(os.times()[4])}.pdf"

    # User-specific upload directory
    user_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], f"user_{user.id}")
    os.makedirs(user_upload_dir, exist_ok=True)
    saved_path = os.path.join(user_upload_dir, clean_name)

    try:
        file.save(saved_path)
        file_size = os.path.getsize(saved_path)
        ext = clean_name.rsplit('.', 1)[1].lower() if '.' in clean_name else 'pdf'

        # Extract, Clean, Chunk
        chunks_data, total_pages = DocumentProcessor.process_file(saved_path, clean_name)

        if not chunks_data:
            flash(f'Warning: Could not extract readable text from "{clean_name}". The file might be empty or scanned images.', 'warning')

        doc_record = Document(
            user_id=user.id,
            filename=clean_name,
            file_path=saved_path,
            file_size=file_size,
            file_type=ext,
            total_pages=total_pages
        )
        db.session.add(doc_record)
        db.session.flush()

        for c in chunks_data:
            chunk = DocumentChunk(
                document_id=doc_record.id,
                chunk_text=c['chunk_text'],
                page_number=c['page_number'],
                chunk_index=c['chunk_index']
            )
            db.session.add(chunk)

        # Log study activity
        activity = StudyActivity(
            user_id=user.id,
            activity_type='upload',
            duration=5,
            details=f"Uploaded and processed {clean_name} ({len(chunks_data)} chunks)"
        )
        db.session.add(activity)
        db.session.commit()

        flash(f'Successfully processed "{clean_name}"! {len(chunks_data)} semantic chunks indexed across {total_pages} page(s).', 'success')
        return redirect(url_for('documents.list_documents'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error processing document: {str(e)}', 'danger')
        return redirect(url_for('documents.list_documents'))

@documents_bp.route('/<int:doc_id>/delete', methods=['POST'])
@login_required
def delete_document(doc_id):
    user = get_current_user()
    doc = Document.query.filter_by(id=doc_id, user_id=user.id).first()

    if not doc:
        flash('Document not found or unauthorized access.', 'danger')
        return redirect(url_for('documents.list_documents'))

    filename = doc.filename
    try:
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
    except Exception as e:
        print(f"Error removing file from disk: {e}")

    db.session.delete(doc)
    db.session.commit()

    flash(f'Document "{filename}" and its indexed knowledge chunks were removed.', 'info')
    return redirect(url_for('documents.list_documents'))

@documents_bp.route('/<int:doc_id>/chunks', methods=['GET'])
@login_required
def view_chunks(doc_id):
    user = get_current_user()
    doc = Document.query.filter_by(id=doc_id, user_id=user.id).first()
    if not doc:
        return jsonify({'error': 'Document not found'}), 404

    return jsonify({
        'document': doc.to_dict(),
        'chunks': [c.to_dict() for c in doc.chunks]
    })
