rule all:
    input:
        "pixecog.bib"
    shell:
        "echo 'All done!'"

rule fetch:
    input:
        "metadata"
    output:
        "fetched_pdfs.txt"
    shell:
        "python code/fetch.py"
    #LINK: ./code/fetch.py

rule merge:
    input:
        "fetched_pdfs"
    output:
        "pixecog.bib"
    shell:
        "python code/merge.py"

rule extract_figures:
    shell:
        "python code/extract_figures.py"