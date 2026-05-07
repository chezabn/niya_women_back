# --- Sujets d'emails (Suite) ---
EMAIL_SUBJECT_VERIFICATION_APPROVED = (
    "Félicitations ! Votre compte Niyya Women est validé 🎉"
)
EMAIL_SUBJECT_VERIFICATION_REJECTED = (
    "Concernant votre demande de vérification Niyya Women"
)

# --- Corps d'emails (Suite) ---

EMAIL_BODY_VERIFICATION_APPROVED = """Bonjour {first_name},

Nous avons le plaisir de t'annoncer que ta demande de vérification d'identité a été acceptée ! ✅

Ton profil a été validé par notre équipe. Tu es désormais officiellement membre de la communauté Niyya Women.

🔓 Ton compte est maintenant entièrement activé.
Tu peux dès maintenant :
- Compléter ton profil.
- Découvrir les publications de la communauté.
- Interagir avec les autres membres.

Merci de ta confiance et bienvenue parmi nous ! 🌸

L'équipe Niyya Women
"""

EMAIL_BODY_VERIFICATION_REJECTED = """Bonjour {first_name},

Nous te remercions d'avoir soumis une demande de vérification d'identité sur Niyya Women.

Après examen attentif de ton dossier par notre équipe, nous sommes au regret de t'informer que ta demande n'a pas pu être validée pour le moment.

📝 Motif :
{rejection_reason}

💡 Que faire maintenant ?
Si tu penses qu'il s'agit d'une erreur ou si tu peux fournir des documents plus clairs (par exemple, un selfie plus lumineux ou une carte d'identité mieux cadrée), tu es invitée à soumettre une nouvelle demande directement depuis ton espace membre.

Nous restons à ta disposition pour toute question.

Bien cordialement,
L'équipe de modération Niyya Women 🌸
"""
