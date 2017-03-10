from yyagl.game import GameLogic
from yyagl.racing.season.season import SingleRaceSeason


class YorgLogic(GameLogic):

    def __init__(self, mdt):
        GameLogic.__init__(self, mdt)
        self.season = None

    def on_start(self):
        GameLogic.on_start(self)
        dev = game.options['development']
        car = dev['car'] if 'car' in dev else ''
        track = dev['track'] if 'track' in dev else ''
        drivers = [(1, 'first name', 'kronos'), (2, 'second name', 'themis'),
                   (3, 'third name', 'diones'), (4, 'fourth name', 'iapeto')]
        self.skills = [(4, -2, -2), (-2, 4, -2), (0, 4, -4), (4, -4, 0),
                  (-2, -2, 4), (-4, 0, 4), (4, 0, -4), (-4, 4, 0)]
        if car and track:
            game.logic.season = SingleRaceSeason(
                ['kronos', 'themis', 'diones', 'iapeto'], car,
                game.logic.skills,
                'assets/images/gui/menu_background.jpg',
                'assets/images/tuning/engine.png',
                'assets/images/tuning/tires.png',
                'assets/images/tuning/suspensions.png',
                ['prototype', 'desert'],
                'assets/fonts/Hanken-Book.ttf')
            game.logic.season.logic.attach(game.event.on_season_end)
            game.logic.season.logic.attach(game.event.on_season_cont)
            skills = [(4, -2, -2), (-2, 4, -2), (0, 4, -4), (4, -4, 0),
                  (-2, -2, 4), (-4, 0, 4), (4, 0, -4), (-4, 4, 0)]
            self.mdt.fsm.demand(
                'Race', 'tracks/' + track, car, drivers, self.skills)
        else:
            self.mdt.fsm.demand('Menu')
