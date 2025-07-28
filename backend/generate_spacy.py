import spacy
from spacy.tokens import DocBin
import srsly

# Load blank pipeline
nlp = spacy.blank("en")
doc_bin = DocBin()

# Read JSONL
for example in srsly.read_jsonl("train_data.jsonl"):
    doc = nlp.make_doc(example["text"])
    doc.cats = example["cats"]
    doc_bin.add(doc)

# Save to disk
doc_bin.to_disk("train.spacy")


#python -m spacy train config.cfg --output ./output --paths.train ./corpus/train.spacy --paths.dev ./corpus/train.spacy
