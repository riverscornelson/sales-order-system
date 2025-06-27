import os
from typing import Dict, Any, Optional
import asyncio
import structlog
import PyPDF2
from email import message_from_string
from email.mime.text import MIMEText
import re
import io

logger = structlog.get_logger()

class DocumentParserAgent:
    """Agent responsible for parsing PDF and email documents"""
    
    def __init__(self):
        self.supported_formats = [".pdf", ".eml", ".msg", ".txt"]
    
    async def parse_document(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse document content based on file type"""
        
        logger.info("Starting document parsing", filename=filename)
        
        # Determine file type
        file_ext = os.path.splitext(filename.lower())[1]
        
        if file_ext == ".pdf":
            return await self._parse_pdf(content, filename)
        elif file_ext in [".eml", ".msg"]:
            return await self._parse_email(content, filename)
        elif file_ext == ".txt":
            return await self._parse_text(content, filename)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    async def _parse_pdf(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse PDF document using PyPDF2"""
        
        try:
            # Convert content to bytes if it's a string (for base64 decoded content)
            if isinstance(content, str):
                content_bytes = content.encode('latin-1')  # PyPDF2 works better with latin-1
            else:
                content_bytes = content
            
            # Open PDF document
            pdf_stream = io.BytesIO(content_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            
            text_content = ""
            tables = []  # Simple table extraction not available in PyPDF2
            metadata = {}
            
            # Extract text from each page
            for page_num, page in enumerate(pdf_reader.pages):
                # Extract text
                page_text = page.extract_text()
                text_content += f"\n--- Page {page_num + 1} ---\n"
                text_content += page_text
            
            # Get document metadata
            if pdf_reader.metadata:
                metadata = {
                    "title": pdf_reader.metadata.get("/Title", ""),
                    "author": pdf_reader.metadata.get("/Author", ""),
                    "subject": pdf_reader.metadata.get("/Subject", ""),
                    "creator": pdf_reader.metadata.get("/Creator", ""),
                    "producer": pdf_reader.metadata.get("/Producer", ""),
                    "creation_date": str(pdf_reader.metadata.get("/CreationDate", "")),
                    "modification_date": str(pdf_reader.metadata.get("/ModDate", ""))
                }
            
            # Post-process text
            cleaned_text = self._clean_text(text_content)
            
            result = {
                "raw_text": cleaned_text,
                "document_type": "pdf",
                "pages": len(pdf_reader.pages),
                "tables": tables,
                "metadata": metadata,
                "text_length": len(cleaned_text)
            }
            
            logger.info("PDF parsing completed", 
                       filename=filename, 
                       pages=len(pdf_reader.pages),
                       text_length=len(cleaned_text))
            
            return result
            
        except Exception as e:
            logger.error("PDF parsing failed", filename=filename, error=str(e))
            raise Exception(f"Failed to parse PDF: {str(e)}")
    
    async def _parse_email(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse email content"""
        
        try:
            # Parse email message
            msg = message_from_string(content)
            
            # Extract headers
            headers = {
                "from": msg.get("From"),
                "to": msg.get("To"),
                "subject": msg.get("Subject"),
                "date": msg.get("Date"),
                "message_id": msg.get("Message-ID")
            }
            
            # Extract body content
            body_text = ""
            attachments = []
            
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))
                    
                    # Extract text content
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_text += payload.decode('utf-8', errors='ignore')
                    
                    # Track attachments
                    elif "attachment" in content_disposition:
                        filename_attach = part.get_filename()
                        if filename_attach:
                            attachments.append({
                                "filename": filename_attach,
                                "content_type": content_type,
                                "size": len(part.get_payload(decode=True) or b"")
                            })
            else:
                # Single part message
                payload = msg.get_payload(decode=True)
                if payload:
                    body_text = payload.decode('utf-8', errors='ignore')
            
            # Clean the text
            cleaned_text = self._clean_text(body_text)
            
            result = {
                "raw_text": cleaned_text,
                "document_type": "email",
                "headers": headers,
                "attachments": attachments,
                "text_length": len(cleaned_text)
            }
            
            logger.info("Email parsing completed", 
                       filename=filename,
                       text_length=len(cleaned_text),
                       attachments=len(attachments))
            
            return result
            
        except Exception as e:
            logger.error("Email parsing failed", filename=filename, error=str(e))
            raise Exception(f"Failed to parse email: {str(e)}")
    
    async def _parse_text(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse plain text content"""
        
        try:
            # Clean the text
            cleaned_text = self._clean_text(content)
            
            result = {
                "raw_text": cleaned_text,
                "document_type": "text",
                "text_length": len(cleaned_text)
            }
            
            logger.info("Text parsing completed", 
                       filename=filename,
                       text_length=len(cleaned_text))
            
            return result
            
        except Exception as e:
            logger.error("Text parsing failed", filename=filename, error=str(e))
            raise Exception(f"Failed to parse text: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double newline
        text = re.sub(r'[ \t]+', ' ', text)      # Multiple spaces/tabs to single space
        
        # Remove common PDF artifacts
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)  # Control characters
        
        # Normalize quotes and dashes
        text = re.sub(r'["""]', '"', text)
        text = re.sub(r"[''']", "'", text)
        text = re.sub(r'[–—]', '-', text)
        
        # Remove page numbers (common pattern)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        
        # Remove email headers that might interfere with extraction
        text = re.sub(r'^(From|To|Subject|Date|Message-ID):.*?\n', '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _extract_layout_information(self, page) -> Dict[str, Any]:
        """Extract layout information from PDF page (for future use)"""
        
        layout_info = {
            "text_blocks": [],
            "images": [],
            "lines": []
        }
        
        try:
            # Get text blocks with position information
            blocks = page.get_text("dict")
            for block in blocks.get("blocks", []):
                if "lines" in block:  # Text block
                    for line in block["lines"]:
                        for span in line["spans"]:
                            layout_info["text_blocks"].append({
                                "text": span["text"],
                                "bbox": span["bbox"],
                                "font": span["font"],
                                "size": span["size"]
                            })
            
            # Get images
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                layout_info["images"].append({
                    "index": img_index,
                    "xref": img[0],
                    "bbox": page.get_image_bbox(img)
                })
            
            # Get lines and shapes
            drawings = page.get_drawings()
            for drawing in drawings:
                layout_info["lines"].append({
                    "items": drawing["items"],
                    "bbox": drawing.get("rect")
                })
                
        except Exception as e:
            logger.debug("Layout extraction failed", error=str(e))
        
        return layout_info