from django.db import models

from django.utils import timezone
from datetime import timedelta

from django.contrib.auth import get_user_model
User = get_user_model()

class Theater(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'owner'}) 
    
    class Meta:
        unique_together = ('name', 'location')
   
    def __str__(self):
        return f"{self.name} - {self.location}"



class Movie(models.Model):
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    duration_minutes = models.IntegerField(default=120)
    language = models.CharField(max_length=50, blank=True, null=True)
    release_date = models.DateField(default=timezone.now, blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'owner'}) 
    class Meta:
        unique_together = ('title', 'language','release_date','owner')
    def __str__(self):
        return self.title



class Show(models.Model):
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE, related_name='shows')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='shows')
    start_time = models.TimeField()
    end_time = models.TimeField()
    date = models.DateField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'owner'})
    
    class Meta:
        unique_together = ('theater', 'movie','start_time','end_time','date','owner')
    
    def __str__(self):
        return f"{self.movie.title} at {self.theater.name} on {self.date}"

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)
        if creating:
            rows = "ABCDEFGHIJ"
            for row in rows:
                for col in range(1, 11):
                    Seat.objects.create(
                        show=self,
                        row=row,
                        column=col,
                        is_booked=False
                    )


class Seat(models.Model):
    show = models.ForeignKey(Show, on_delete=models.CASCADE, related_name='seats')
    row = models.CharField(max_length=1)
    column = models.PositiveIntegerField()
    is_booked = models.BooleanField(default=False)

    class Meta:
        unique_together = ('show', 'row', 'column')

    def __str__(self):
        return f"{self.row}{self.column} - {self.show}"