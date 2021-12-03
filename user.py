class Users:
    """
    Модель пользователя, предназначена для хранения текущих значений запросов каждого пользователя.
    Классовый атрибут users предназначен для хранения всех пользователей.
    """
    users = dict()

    def __init__(self, user_id: int):
        self.user_id: int = user_id
        Users.add_user(user_id=user_id, user=self)
        self.command: str = ''
        self.city: str = ''
        self.hotels_number: int = 0
        self.uploading_photos: bool = False
        self.number_photos: int = 0
        self.max_price: int = 0
        self.max_distance: int = 0
        self.arrival_date = ''
        self.departure_date = ''

    @classmethod
    def add_user(cls, user_id: int, user: 'Users') -> None:
        cls.users[user_id] = user

    @classmethod
    def get_user(cls, user_id: int) -> 'Users':
        if user_id in cls.users:
            return cls.users[user_id]
        Users(user_id=user_id)
        return cls.users[user_id]
