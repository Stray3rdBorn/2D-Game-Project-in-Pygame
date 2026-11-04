from django.db import models


class Score(models.Model):
    user_id = models.IntegerField()
    player_name = models.CharField(max_length=20)
    score = models.IntegerField()
    wave_reached = models.IntegerField()
    won = models.BooleanField()
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "scores"
        ordering = ["-score", "created_at"]

    def __str__(self):
        return f"{self.player_name}: {self.score}"