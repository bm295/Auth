import random
from dataclasses import dataclass, field
from typing import List

NAMES = [
    "An", "Bình", "Cường", "Dũng", "Hải", "Hùng",
    "Khoa", "Linh", "Minh", "Nam", "Phúc", "Quân",
    "Sơn", "Tài", "Tuấn", "Vinh"
]

@dataclass
class Player:
    name: str
    rating: int

@dataclass
class Team:
    name: str
    players: List[Player] = field(default_factory=list)

    @property
    def avg_rating(self) -> float:
        if not self.players:
            return 0
        return sum(p.rating for p in self.players) / len(self.players)

class ManagerGame:
    def __init__(self):
        self.user_team = Team("My FC", self.generate_players())
        self.ai_teams = [Team(f"AI FC {i+1}", self.generate_players()) for i in range(3)]
        self.history: List[str] = []

    def generate_players(self) -> List[Player]:
        players = []
        for _ in range(11):
            name = random.choice(NAMES)
            rating = random.randint(60, 90)
            players.append(Player(name, rating))
        return players

    def play_match(self):
        opponent = random.choice(self.ai_teams)
        user_score = self._calculate_score(self.user_team.avg_rating)
        opp_score = self._calculate_score(opponent.avg_rating)
        result = f"{self.user_team.name} {user_score} - {opp_score} {opponent.name}"
        self.history.append(result)

    def _calculate_score(self, avg_rating: float) -> int:
        base = avg_rating / 20.0
        score = int(random.random() * base)
        return max(0, min(score, 5))
