import random
from django.db import models
from django.core import validators
from django.core.exceptions import ValidationError


class DifficultyLevel(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text="e.g. Trainee, Idol, Legend")
    multiplier = models.DecimalField(
        max_digits=3, decimal_places=2, default=1.0,
        validators=[validators.MinValueValidator(1.0)]
    )
    color_code = models.CharField(max_length=7, default="#FF007A", help_text="KPOP Neon color for UI")

    class Meta:
        verbose_name_plural = "Difficulty Levels"

    def __str__(self):
        return self.name


class BaseTask_(models.Model):
    title = models.CharField(max_length=100, validators=[validators.MinLengthValidator(5)])
    description = models.TextField(help_text="Describe the mission to the trainee.")
    difficulty = models.ForeignKey(
        DifficultyLevel,
        on_delete=models.PROTECT,
        related_name='%(class)s_tasks'
    )
    base_points = models.PositiveIntegerField(
        default=10,
        validators=[validators.MinValueValidator(1), validators.MaxValueValidator(100)]
    )
    choice_1 = models.CharField(max_length=50, blank=True, null=True)
    choice_2 = models.CharField(max_length=50, blank=True, null=True)
    choice_3 = models.CharField(max_length=50, blank=True, null=True)
    created_by = models.ForeignKey(
        'accounts.TeacherProfile',
        on_delete=models.CASCADE,
        related_name='%(class)s_tasks',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def calculate_total_points(self):
        return int(self.base_points * self.difficulty.multiplier)

    @property
    def correct_answer_value(self):
        return getattr(self, 'correct_answer', getattr(self, 'correct_value', None))

    def get_all_options(self, correct_answer):
        raw_options = [correct_answer, self.choice_1, self.choice_2, self.choice_3]
        options = [str(opt) for opt in raw_options if opt is not None]
        random.shuffle(options)
        return options

    @property
    def get_play_url_name(self):
        prefix = self.__class__.__name__.lower().replace('task', '').replace('challenge', '')
        return f"challenges:{prefix}_play"


    def __str__(self):
        return f"[{self.difficulty.name}] {self.title}"


class BaseTask(BaseTask_):
    class Meta(BaseTask_.Meta):
        abstract = False
        verbose_name = "Base Mission"
        verbose_name_plural = "Base Missions"


class CountingTask(BaseTask):
    image = models.ImageField(upload_to="counting/")
    correct_answer = models.PositiveIntegerField()

    class Meta(BaseTask.Meta):
        verbose_name = "Counting Mission"
        verbose_name_plural = "Counting Missions"

    def check_answer(self, user_input):
        return str(user_input) == str(self.correct_answer)


class ArithmeticTask(BaseTask):
    number_a = models.PositiveIntegerField(
        validators=[validators.MaxValueValidator(100)],
        help_text="First number (e.g., Albums sold in Seoul)"
    )
    number_b = models.PositiveIntegerField(
        validators=[validators.MaxValueValidator(100)],
        help_text="Second number (e.g., Albums sold in Busan)"
    )
    operation = models.CharField(
        max_length=1,
        choices=[('+', 'Addition'), ('-', 'Subtraction')],
        help_text="Choose '+' to combine or '-' to find the difference."
    )
    correct_answer = models.IntegerField(editable=False, null=True, blank=True)

    class Meta(BaseTask.Meta):
        verbose_name = "Arithmetic Mission"
        verbose_name_plural = "Arithmetic Missions"

    def clean(self):
        super().clean()
        if self.operation == '-' and self.number_a < self.number_b:
            raise ValidationError(
                {
                    'number_b': "Oops! For our young trainees, the first number must be "
                                "larger than the second number so the result isn't negative."
                },
                code='negative_result'
            )


    def generate_unique_decoys(self):
        correct = self.correct_answer
        decoys = set()
        while len(decoys) < 3:
            offset = random.choice([-3, -2, -1, 1, 2, 3, 4, 5])
            decoy = correct + offset
            if decoy != correct and decoy >= 0:
                decoys.add(str(decoy))
        return list(decoys)


    def save(self, *args, **kwargs):
        if self.operation == '+':
            self.correct_answer = self.number_a + self.number_b
        else:
            self.correct_answer = self.number_a - self.number_b
        decoys = self.generate_unique_decoys()
        self.choice_1, self.choice_2, self.choice_3 = decoys
        super().save(*args, **kwargs)


    def check_answer(self, user_input):
        return str(user_input) == str(self.correct_answer)


class PatternChallenge(BaseTask):
    sequence_data = models.JSONField(help_text="Example: ['Mic', 'Stage', '?', 'Award']")
    correct_value = models.CharField(max_length=50)

    class Meta(BaseTask.Meta):
        verbose_name = "Pattern Puzzle"
        verbose_name_plural = "Pattern Puzzles"

    def clean(self):
        if '?' not in self.sequence_data:
            raise ValidationError("Sequence must contain a '?' placeholder.")


    def check_answer(self, user_input):
        return str(user_input).strip().lower() == str(self.correct_value).strip().lower()


class MazeTask(BaseTask):
    grid = models.JSONField(help_text="2D array: 0=path, 1=wall")
    start_row = models.PositiveIntegerField(default=0)
    start_col = models.PositiveIntegerField(default=0)
    end_row = models.PositiveIntegerField()
    end_col = models.PositiveIntegerField()

    class Meta(BaseTask.Meta):
        verbose_name = "Maze Navigation"
        verbose_name_plural = "Maze Navigations"

    def check_answer(self, user_input):
        return user_input == "stage clear"

       # ToDo extra games and polish the existing ones