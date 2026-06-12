from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.core.mail import send_mass_mail
from django.db.models import Avg
from django.conf import settings
from .models import Review, Location, Subscription

@receiver(post_save , sender=Review)
@receiver(post_delete, sender=Review)
def update_location_rating(sender, instance, **kwargs):
    location = instance.location
    result = Review.objects.filter(location=location).aggregate(Avg("value"))
    new_rating = result['value__avg'] or 0
    location.rating = round(new_rating, 1)
    location.save()

@receiver(post_save, sender=Review)
def send_review_notification_to_subscribers(sender, instance, **kwargs):
    if not kwargs.get('created'):
        return
    review = instance
    location = review.location
    author = review.user

    subscribers_emails = Subscription.objects.filter(location=location).select_related("user").values_list("user__email", flat=True)

    emails_list = [email for email in subscribers_emails if email]
    if not emails_list:
        return
    subject = f"New review for location '{location.name}'"
    message = f""" Hi
    User {author.username} has left a new review for the location {location.name}, which you follow
    Rating : {review.value}/5
    Review text : 
    {review.text}
    Best regards, our service team.
    """
    datatuple = tuple(
        (subject,message,settings.DEFAULT_FROM_EMAIL, [recipient_email]) for recipient_email in emails_list
    )

    send_mass_mail(datatuple, fail_silently=True)