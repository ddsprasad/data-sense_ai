import pandas as pd
import json
from target_db.database import execute_query_original
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Annoy
from langchain.schema import Document

from util.util import get_full_documentation_split_list
from app_init.smart_schema_discovery import build_enhanced_schema_context, get_sample_data_for_tables, add_sample_data_to_schema


def create_vector_store(keyword_mapping_file):
    """
    Create vector store with automated schema discovery

    Args:
        keyword_mapping_file: JSON file with keyword mappings
                              Each entry: {"keywords": "...", "tables": "...", "related_keywords": "..."}

    Returns:
        vector_store, create_statement_dict
    """

    print("Loading keyword mappings...")
    # Step 1: Read keyword-to-table mappings from JSON
    with open(keyword_mapping_file, 'r') as f:
        docs_data = json.load(f)

    # Step 2: Extract unique table names
    print("Discovering tables...")
    table_names = []
    for entry in docs_data:
        tables_row = entry['tables']
        tables_list = tables_row.split(',')
        for table_name in tables_list:
            clean_name = table_name.strip()
            if clean_name and clean_name not in table_names:
                table_names.append(clean_name)

    print(f"   Found {len(table_names)} unique tables: {', '.join(table_names)}")

    # Step 3: AUTO-DISCOVER schema with relationships
    print("Auto-discovering database schema (tables, columns, PKs, FKs)...")
    create_statement_dict = build_enhanced_schema_context(table_names)

    # Step 4: AUTO-FETCH sample data
    print("Fetching sample data...")
    sample_data_dict, column_names_dict = get_sample_data_for_tables(table_names)

    # Step 5: Combine schema + sample data
    print("Building enhanced schema context...")
    create_statement_dict = add_sample_data_to_schema(
        create_statement_dict,
        sample_data_dict,
        column_names_dict
    )

    # Step 6: Create metadata for vector store
    print("Creating metadata cache...")
    metadata_list = []
    for entry in docs_data:
        metadata_str = f"[Tables] - {entry['tables']}; [Related Keywords] - {entry['related_keywords']}"
        metadata_list.append({
            'Keywords': entry['keywords'],
            'metadata': metadata_str
        })

    # Save cache (optional - for debugging)
    with open('meta.json', 'w') as f:
        json.dump(metadata_list, f, indent=2)
    print("   Cached to meta.json")

    # Step 7: Create vector store
    print("Building vector store with embeddings...")
    embeddings_func = HuggingFaceEmbeddings()
    metadata_docs = [
        Document(
            page_content=item['Keywords'],
            metadata={"metadata": item['metadata']}
        ) for item in metadata_list
    ]

    vector_store = Annoy.from_documents(metadata_docs, embeddings_func)
    print("Vector store created successfully!\n")

    return vector_store, create_statement_dict


def create_rag_vector_store():
    """Create RAG vector store for documentation"""
    embeddings_func = HuggingFaceEmbeddings()
    sections = get_full_documentation_split_list()
    metadata_docs = [
        Document(page_content=section, metadata={"metadata": section})
        for section in sections
    ]
    vector_store_for_rag = Annoy.from_documents(metadata_docs, embeddings_func)
    return vector_store_for_rag
