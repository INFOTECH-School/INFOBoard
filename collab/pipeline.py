import requests
from django.contrib import messages
from django.core.files.base import ContentFile
from django.utils.timezone import now

def update_profile_picture(backend, user, response, *args, **kwargs):
    """
    Pipeline function that updates the user's profile picture from the authentication provider.
    This function is intended to be added to your SOCIAL_AUTH_PIPELINE.
    """
    # Check that we are using Google OAuth2
    if backend.name != 'google-oauth2':
        return

    # Retrieve the profile picture URL from the response
    picture_url = response.get('picture')
    if not picture_url:
        return

    try:
        r = requests.get(picture_url, timeout=5)
        if r.status_code == 200:
            # Create a unique filename for the profile picture, e.g. "profile_<user.pk>_<timestamp>.jpg"
            file_name = f"profile_{user.pk}_{now().strftime('%Y%m%d%H%M%S')}.jpg"
            # Save the image content to the user's profile_picture field without immediately saving the model
            user.profile_image.save(file_name, ContentFile(r.content), save=False)
            user.save()
    except requests.RequestException:
        # Optionally log the error here
        pass
