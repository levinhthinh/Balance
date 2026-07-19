from django.conf import settings
from django.db import models
from main.models import Account, Type


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    default_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and self.default_account_id is None:
            account = Account.objects.create(
                user=self.user,
                title=Type.personal.label,
                account_type=Type.personal,
            )
            self.default_account = account
            super().save(update_fields=['default_account'])


from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

