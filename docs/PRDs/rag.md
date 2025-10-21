#Overview
Rag is the fundamental unit of what memic.ai does. We have a robust RAG system which helps developers get started with their semantic search needs in no time. Our meticulosly designed RAG helps industries like Law, Finance and others to store their business context and documents in a way which will help them collaboarate and build new documents not in silos but using shared and always updated business context.


#HLD
The RAG mainly involves a 4 step design
1)File conversion: A file is uploaded to memic, we have our main parsers - PDF parser and EXCEL parser, we convert doc, txt, email and markdown files to pdf and use the excel parser for the same. We store both the Raw file and the converted file if needed in the blob storage.
2)Parsing: In this step, we will extract the contents of the file using Azure AFR or any other similar parser. We have an inhouse proprietary algorithm to break the file into smaller parts known as sections. we store information like the bounding box for a section, the type of data in a section, is it a paragraph, a table, an image, etc. The output of parsing step is an enriched JSON file while explains the file for AI models better. Both the RAW file and the enriched JSON is stored in blob storage and we index the same in postgres.
3) Chunking: This is the step where the larger file is broken down into smaller chunks where the Enriched JSON is the input and we try to make sure each chunk is as information complete as possible. The Enterprise customers will have an option to adjust the chunk size, etc. We store these chunks in a blob storage with indexing in the postgres DB
4) Embedding: Each of these chunks are then embedded using an embedding model and the embedding are stored in a vector database with relevant metadata fields to be able to retrieve with minimal latencies.

Once all the above steps are ready, the file is indexed and ready to be retrieved. 

Any file that get's injested goes through below stages:
* uploading
* uploaded
* uploading failed
* file conversion started (optional)
* file conversion complete (optional)
* file conversion failed (optional)
* Parsing started
* Parsing complete
* Parsing failed
* Enrichment started
* Enrichment complete
* Enrichment failed
* Chunking started
* Chunking complete
* Chunking failed
* embedding started
* embedding complete
* embedding failed
* ready

#Blob storage structure
The files in blob storage follow the below hierarchy for easier isolation for organisations and easier pin pointing and path identification. One of the below ways, we'll decide on the best (TBD)

appraoch1: orgnaisation_id_name > project_id_name > file_id > raw/converted/enriched/chunks/embeddings

approach 2: orgnaisation_id_name > project_id_name > raw/converted/enriched/chunks/embeddings > file_id


#LLD
Below points explain the entity design for the files and their related data

we already have these entities:
* organisation
* project

New entities:
* files: files belong to project
- id, name, size, type, blob_location, is_converted, converted, file_location, enriched_file_location, created_at, updated_at

* file_metadata (tbd) - metadata support for dev teams to store for each file. key value pairs
- id, file_id, metadata(json)

* file_chunk: chunks for each file
- id, file_id, chunk_location, created_at, updated_at
