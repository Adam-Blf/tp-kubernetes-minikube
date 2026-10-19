"""Transforme les sorties brutes de preuves/ en captures PNG légendées, aux couleurs EFREI.

Usage : python scripts/render_preuves.py [dossier_preuves]
Chaque .txt est la sortie réelle de scripts/rejouer_tp.sh ; le PNG en est le rendu
fidèle, avec une légende. Les captures navigateur (Chrome sans interface) sont
encadrées et légendées de la même façon. Les états de Pod sont colorés.
"""
import os
import sys
import textwrap

from PIL import Image, ImageDraw, ImageFont

# Ordre et numéros des figures = ordre du TP ; les noms de fichiers suivent les livrables.
TERMINAL = {
    "01-cluster": "Figure 1 - Démarrage et inspection du cluster Minikube (versions, statut, nœud, pods système)",
    "06-pod-autonome": "Figure 2 - Pod autonome : inspection, hostname, suppression sans recréation",
    "02-deployment": "Figure 3 - Deployment whoami : 3 réplicas, ReplicaSet, labels et describe",
    "03-autoreparation": "Figure 4 - Auto-réparation : le Pod supprimé (Terminating) à côté de son remplaçant",
    "03b-mise-a-l-echelle": "Figure 5 - Mise à l'échelle : 3 puis 5, 0 et retour à 3 Pods",
    "04-service-http": "Figure 6 - Service whoami-service, endpoints et réponse HTTP via port-forward 8080",
    "05-image-personnalisee": "Figure 8 - Image monapp:1.0 chargée dans Minikube, Deployment et page servie (8081)",
    "10-nettoyage": "Figure 10 - Nettoyage : ressources et namespace demo supprimés, minikube stop",
}
BROWSER = {
    "04b-navigateur-whoami": ("http://localhost:8080", "Figure 7 - whoami vu dans le navigateur, via le Service (port-forward 8080)"),
    "05b-navigateur-monapp": ("http://localhost:8081", "Figure 9 - Page monapp vue dans le navigateur (port-forward 8081)"),
}

# Charte EFREI (efrei.fr) : navy, bleu primaire, rose signature.
NAVY, BLEU, ROSE = "#051832", "#163767", "#FF43B8"
FOND, TEXTE, MUTED = "#0B1B34", "#DDE5F0", "#8FA3BF"
WIN = "C:/Windows/Fonts/"
USER_FONTS = os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/")
STATE_COLORS = (
    ("Terminating", "#FF7B9C"),
    ("DELETED", "#FF7B9C"),
    ("ContainerCreating", "#F2C14E"),
    ("Pending", "#F2C14E"),
    ("ADDED", "#5BD38A"),
)
WRAP = 130
LH, PAD, BAR = 22, 24, 44


def _font(candidates, size):
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


MONO = _font([WIN + "consola.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"], 16)
MONO_B = _font([WIN + "consolab.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"], 16)
TITRE = _font([USER_FONTS + "Gilroy-ExtraBold.otf", WIN + "segoeuib.ttf"], 21)
MARQUE = _font([USER_FONTS + "Gilroy-ExtraBold.otf", WIN + "segoeuib.ttf"], 15)
BARRE = _font([USER_FONTS + "Gilroy-Light.otf", WIN + "segoeui.ttf"], 15)


def _frame(width: int, height: int, label: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (width, height), FOND)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, width, BAR], fill=BLEU)
    draw.rectangle([0, BAR, width, BAR + 3], fill=ROSE)
    draw.text((PAD, 13), "EFREI", font=MARQUE, fill=ROSE)
    draw.text((PAD + 70, 14), label, font=BARRE, fill=TEXTE)
    return img, draw


def render_terminal(folder: str, name: str, caption: str) -> None:
    src = os.path.join(folder, name + ".txt")
    if not os.path.exists(src):
        print("absent :", src)
        return
    raw = open(src, encoding="utf-8").read().rstrip().split("\n")
    # Les messages d'erreur très longs sont repliés pour garder une capture lisible.
    lines = [p for l in raw for p in (textwrap.wrap(l, WRAP, subsequent_indent="    ") or [""])]
    width = max(900, max(int(MONO.getlength(l)) for l in lines), int(TITRE.getlength(caption))) + 2 * PAD
    height = BAR + 3 + PAD * 2 + 40 + LH * len(lines)
    img, draw = _frame(width, height, "terminal - minikube, namespace demo")
    y = BAR + 3 + PAD
    draw.text((PAD, y), caption, font=TITRE, fill=TEXTE)
    y += LH + 18
    for line in lines:
        if line.startswith("$ "):
            draw.text((PAD, y), "$", font=MONO_B, fill=ROSE)
            draw.text((PAD + 24, y), line[2:], font=MONO_B, fill="#FFFFFF")
        elif line.startswith("#"):
            draw.text((PAD, y), line, font=MONO, fill="#7FC4EC")
        else:
            color = next((c for k, c in STATE_COLORS if k in line), TEXTE)
            draw.text((PAD, y), line, font=MONO, fill=color)
        y += LH
    img.crop((0, 0, width, y + 20)).save(os.path.join(folder, name + ".png"))
    print(name, img.size)


def render_browser(folder: str, name: str, url: str, caption: str) -> None:
    """Encadre une capture Chrome brute (<name>-brut.png) avec barre d'adresse et légende."""
    src = os.path.join(folder, name + "-brut.png")
    if not os.path.exists(src):
        print("absent :", src)
        return
    shot = Image.open(src).convert("RGB")
    width = shot.width + 2 * PAD
    top = BAR + 3 + PAD + LH + 18 + 40
    img, draw = _frame(width, top + shot.height + PAD, "navigateur - Chrome")
    y = BAR + 3 + PAD
    draw.text((PAD, y), caption, font=TITRE, fill=TEXTE)
    y += LH + 18
    draw.rounded_rectangle([PAD, y, width - PAD, y + 30], radius=15, fill=NAVY, outline=MUTED)
    draw.text((PAD + 16, y + 6), url, font=MONO, fill=TEXTE)
    img.paste(shot, (PAD, top))
    img.save(os.path.join(folder, name + ".png"))
    print(name, img.size)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "preuves")
    for key, cap in TERMINAL.items():
        render_terminal(target, key, cap)
    for key, (url, cap) in BROWSER.items():
        render_browser(target, key, url, cap)
