"""Transforme les sorties brutes de preuves/*.txt en captures PNG légendées.

Usage : python scripts/render_preuves.py [dossier_preuves]
Chaque .txt est la sortie réelle de scripts/rejouer_tp.sh ; le PNG en est le rendu
fidèle, avec une légende. Les états de Pod sont colorés pour être lus d'un coup d'oeil.
"""
import os
import sys
import textwrap

from PIL import Image, ImageDraw, ImageFont

CAPTIONS = {
    "01-cluster": "Figure 1 - Démarrage et inspection du cluster Minikube (versions, statut, nœud, pods système)",
    "02-deployment": "Figure 2 - Deployment whoami : 3 réplicas, ReplicaSet, labels et describe",
    "03-autoreparation": "Figure 3 - Auto-réparation : le Pod supprimé (Terminating) à côté de son remplaçant",
    "03b-mise-a-l-echelle": "Figure 3b - Mise à l'échelle : 3 puis 5, 0 et retour à 3 Pods",
    "04-service-http": "Figure 4 - Service whoami-service, endpoints et réponse HTTP via port-forward 8080",
    "05-image-personnalisee": "Figure 5 - Image monapp:1.0 chargée dans Minikube, Deployment et page servie (8081)",
    "06-pod-autonome": "Figure 6 - Pod autonome : inspection, hostname, suppression sans recréation",
    "10-nettoyage": "Figure 7 - Nettoyage : ressources et namespace demo supprimés, minikube stop",
}
FONTS = "C:/Windows/Fonts/" if os.name == "nt" else "/usr/share/fonts/truetype/dejavu/"
REG = "consola.ttf" if os.name == "nt" else "DejaVuSansMono.ttf"
BOLD = "consolab.ttf" if os.name == "nt" else "DejaVuSansMono-Bold.ttf"
WRAP = 130
STATE_COLORS = (
    ("Terminating", "#ff7b72"),
    ("ContainerCreating", "#d29922"),
    ("Pending", "#d29922"),
    ("DELETED", "#ff7b72"),
    ("ADDED", "#3fb950"),
)


def render(folder: str, name: str, caption: str) -> None:
    src = os.path.join(folder, name + ".txt")
    if not os.path.exists(src):
        print("absent :", src)
        return
    font = ImageFont.truetype(FONTS + REG, 16)
    bold = ImageFont.truetype(FONTS + BOLD, 16)
    title = ImageFont.truetype(FONTS + BOLD, 20)
    raw = open(src, encoding="utf-8").read().rstrip().split("\n")
    # Les messages d'erreur très longs sont repliés pour garder une capture lisible.
    lines = [p for l in raw for p in (textwrap.wrap(l, WRAP, subsequent_indent="    ") or [""])]
    lh, pad = 22, 24
    width = max(900, max(int(font.getlength(l)) for l in lines), int(title.getlength(caption))) + 2 * pad
    height = pad * 2 + 40 + lh * len(lines) + 40
    img = Image.new("RGB", (width, height), "#0d1117")
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, width, 40], fill="#161b22")
    for i, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        draw.ellipse([14 + i * 22, 13, 26 + i * 22, 25], fill=color)
    draw.text((95, 9), "terminal - minikube (namespace demo)", font=font, fill="#8b949e")
    y = 40 + pad
    draw.text((pad, y), caption, font=title, fill="#58a6ff")
    y += lh + 14
    for line in lines:
        if line.startswith("$ "):
            draw.text((pad, y), "$", font=bold, fill="#3fb950")
            draw.text((pad + 24, y), line[2:], font=bold, fill="#e6edf3")
        elif line.startswith("#"):
            draw.text((pad, y), line, font=font, fill="#d29922")
        else:
            color = next((c for k, c in STATE_COLORS if k in line), "#c9d1d9")
            draw.text((pad, y), line, font=font, fill=color)
        y += lh
    img.crop((0, 0, width, y + 20)).save(os.path.join(folder, name + ".png"))
    print(name, img.size)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "preuves")
    for key, cap in CAPTIONS.items():
        render(target, key, cap)
