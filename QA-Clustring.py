import streamlit as st
import xml.etree.ElementTree as ET
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import pandas as pd

st.title("📊 Analyse intelligente des erreurs QA (Robot Framework)")

uploaded_file = st.file_uploader("Choisis ton fichier output.xml", type="xml")

def extract_failures(root):
    failures = []
    for status in root.findall(".//status[@status='FAIL']"):
        if status.text and status.text.strip():
            failures.append(status.text.strip())
    return failures

def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def simplify_message(msg, max_len=300):
    msg = re.sub(r'Stacktrace:.*', '', msg, flags=re.DOTALL)
    msg = re.sub(r'\s+', ' ', msg).strip()
    return msg[:max_len] + "..." if len(msg) > max_len else msg

if uploaded_file:
    tree = ET.parse(uploaded_file)
    root = tree.getroot()

    failures = extract_failures(root)
    cleaned = [clean_text(f) for f in failures]

    if failures:
        vectorizer = TfidfVectorizer()
        X = vectorizer.fit_transform(cleaned)
        n_clusters = min(3, len(failures))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        kmeans.fit(X)

        grouped = {}
        for i, label in enumerate(kmeans.labels_):
            grouped.setdefault(label, []).append(failures[i])

        st.success(f"{len(failures)} erreurs détectées.")
        for label, msgs in grouped.items():
            st.subheader(f"🧠 Groupe {label+1} ({len(msgs)} erreurs)")
            for i, m in enumerate(msgs, 1):
                st.markdown(f"**{i}.** {simplify_message(m)}")

        # Export CSV
        data = []
        for label, msgs in grouped.items():
            for msg in msgs:
                data.append({
                    "Groupe": f"Groupe {label+1}",
                    "Erreur simplifiée": simplify_message(msg),
                    "Erreur complète": msg
                })
        df = pd.DataFrame(data)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Télécharger CSV", csv, "grouped_errors.csv", "text/csv")
    else:
        st.warning("Aucune erreur détectée dans le fichier.")
