"""
nnBreakout
"""
import sys
import pygame
import abc
import math
import utils
from constants import *
import copy
import time
import random


class Breakout(object):
    """
    Abstract base class for breakout

    Implements basically all of the game logic. The only thing that remains
       for subclasses to flesh out is the run() method
    """

    def __init__(self, csv, verbose, display, batches, write_model=False, model_path=None):
        self.batches = batches
        self.csv = csv
        self.verbose = verbose
        self.display = display
        self.write_model = write_model
        self.model_path = model_path
        self.hit_ball = False
        self.experience = []

        pygame.init()

        if self.display:
            self.screen = pygame.display.set_mode(SCREEN_SIZE)
            pygame.display.set_caption("Breakout!!")

        self.clock = pygame.time.Clock()

        if pygame.font:
            self.font = pygame.font.Font(None, 30)
        else:
            self.font = None

        self.init_game()

        # play music!!!!1 except pygame doesn't like mp3's?? TODO fix (low priority)
        # pygame.mixer.music.load('static/audio/FUTUREWORLD.mp3')
        # pygame.mixer.music.play(-1)

    def init_game(self):
        """ set game params """
        self.lives = 1
        self.score = 0
        self.num_hits = 0
        self.boosts_remaining = 3
        self.boost_time = 0
        self.speed_multiplyer = 1.0
        self.time = 0
        self.game_state = STATE_BALL_IN_PADDLE
        self.paddle = pygame.Rect(300, PADDLE_Y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.ball = pygame.Rect(
            300, PADDLE_Y - BALL_DIAMETER, BALL_DIAMETER, BALL_DIAMETER)
        self.ball_vel = [5, 5]    # [x, y]
        self.game_won = False
        self.create_bricks()

    def create_bricks(self):
        """ creates smashable targets """
        y_ofs = 60
        self.bricks = []
        for i in range(6):
            x_ofs = 10
            for j in range(9):
                self.bricks.append(pygame.Rect(
                    x_ofs, y_ofs, BRICK_WIDTH, BRICK_HEIGHT))
                x_ofs += BRICK_WIDTH + 10
            y_ofs += BRICK_HEIGHT + 5

    def draw_bricks(self):
        for brick in self.bricks:
            pygame.draw.rect(self.screen, BRICK_COLOR, brick)

    def take_input(self, input):
        """ takes a vector of game inputs and applies them to game objects """
        boost = 5 if self.boost_time > 0 else 0

        if INPUT_L in input:
            self.set_paddle_pos(self.paddle.left - (7 + boost))

        if INPUT_R in input:
            self.set_paddle_pos(self.paddle.left + (7 + boost))

        if INPUT_B in input and self.boosts_remaining > 0 and self.boost_time == 0:
            self.boosts_remaining -= 1
            self.boost_time += 25

        if INPUT_SPACE in input and self.game_state == STATE_BALL_IN_PADDLE:
            angle_initial = ((random.random()-0.5)*90)/180*3.14
            initial_y_vel = 5*math.cos(angle_initial)
            initial_x_vel = 5*math.sin(angle_initial)
            self.ball_vel = [initial_x_vel, initial_y_vel]
            # self.ball_vel = [5,5]
            self.speed_multiplyer = 1.0
            self.game_state = STATE_PLAYING

        if INPUT_QUIT in input:
            self.game_state = STATE_GAME_OVER
            self.set_paddle_pos(300)

        elif INPUT_ENTER in input and (self.game_state == STATE_GAME_OVER or self.game_state == STATE_WON):
            self.init_game()

    def set_paddle_pos(self, x):
        self.paddle.left = x
        if self.paddle.left < 0:
            self.paddle.left = 0
        elif self.paddle.left > MAX_PADDLE_X:
            self.paddle.left = MAX_PADDLE_X

    def move_ball(self):
        """ applies ball velocity vector to ball """
        self.ball.x += self.ball_vel[0] * self.speed_multiplyer
        # pygame treats "up" as decreasing y axis
        self.ball.y -= self.ball_vel[1] * self.speed_multiplyer

        if self.ball.left <= 0:
            self.ball.left = 0
            self.ball_vel[0] = -self.ball_vel[0]
        elif self.ball.left >= MAX_BALL_X:
            self.ball.left = MAX_BALL_X
            self.ball_vel[0] = -self.ball_vel[0]

        if self.ball.top < 0:
            self.ball.top = 0
            self.ball_vel[1] = -self.ball_vel[1]
        elif self.ball.top >= MAX_BALL_Y:
            self.ball.top = MAX_BALL_Y
            self.ball_vel[1] = -self.ball_vel[1]

    def handle_collisions(self):
        """ logic for collision between ball and game object """
        for brick in self.bricks:
            if self.ball.colliderect(brick):
                # only allow points after first brick is broken
                if len(self.bricks) < 6 * 9:
                    self.score += BROKEN_BRICK_PTS
                self.num_hits += 1
                if (brick.x > self.ball.x - self.ball_vel[0] * self.speed_multiplyer + BALL_DIAMETER)\
                        or (brick.x + BRICK_WIDTH < self.ball.x - self.ball_vel[0] * self.speed_multiplyer):
                    self.ball_vel[0] = -self.ball_vel[0]
                else:
                    self.ball_vel[1] = -self.ball_vel[1]
                self.bricks.remove(brick)
                self.speed_multiplyer = min(
                    self.speed_multiplyer + 0.05, MAX_SPEED)
                break

        if len(self.bricks) == 0:
            self.score += 1000
            self.game_state = STATE_WON

        if self.ball.colliderect(self.paddle):
            distance_from_center = float(
                self.ball.centerx - self.paddle.centerx)
            self.ball.top = PADDLE_Y - BALL_DIAMETER
            self.ball_vel[0] += distance_from_center / 7
            self.ball_vel[1] = -self.ball_vel[1]
        elif self.ball.top > self.paddle.top:
            self.lives -= 1
            if self.lives > 0:
                self.game_state = STATE_BALL_IN_PADDLE
                self.ball.left = self.paddle.left + self.paddle.width / 2
                self.ball.top = self.paddle.top - self.ball.height
            else:
                self.game_state = STATE_GAME_OVER

    def execute_turn(self):
        """ 
        logic for a single game turn:
           -move ball
           -display messages (if appropriate)
           -draw game on screen
           -update boost time
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit

        if self.display:
            self.clock.tick(50)
            self.screen.fill(BLACK)

        if self.game_won:
            self.game_state = STATE_GAME_OVER

        if self.game_state == STATE_PLAYING:
            self.time += 1
            self.move_ball()
            self.handle_collisions()
        elif self.game_state == STATE_BALL_IN_PADDLE:
            self.ball.left = self.paddle.left + self.paddle.width / 2
            self.ball.top = self.paddle.top - self.ball.height
            self.show_message("PRESS SPACE TO LAUNCH THE BALL")
            self.show_message("PRESS B TO BOOST", 0, 30)
        elif self.game_state == STATE_GAME_OVER:
            self.show_message("GAME OVER. PRESS ENTER TO PLAY AGAIN")
        elif self.game_state == STATE_WON:
            self.show_message("YOU WON! PRESS ENTER TO PLAY AGAIN")
            # little hack to make game go for one more step after a win
            # (give online agents time to realize it's one and do an update)
            self.game_won = True

        self.boost_time = max(self.boost_time - 1, 0)

        if self.display:
            self.draw_bricks()
            # Draw paddle
            if self.boost_time > 0:
                pygame.draw.rect(self.screen, PINK, self.paddle)
            else:
                pygame.draw.rect(self.screen, BLUE, self.paddle)
            # Draw ball
            pygame.draw.circle(self.screen, WHITE, (self.ball.left +
                               BALL_RADIUS, self.ball.top + BALL_RADIUS), BALL_RADIUS)
            self.show_stats()
            pygame.display.flip()

    def show_stats(self):
        if self.font and self.display:
            font_surface = self.font.render("SCORE: " + str(self.score) + " LIVES: " + str(
                self.lives) + " BOOSTS: " + str(self.boosts_remaining), False, WHITE)
            self.screen.blit(font_surface, (135, 5))

    def show_message(self, message, x_ofs=0, y_ofs=0):
        if self.font and self.display:
            size = self.font.size(message)
            font_surface = self.font.render(message, False, WHITE)
            x = ((SCREEN_SIZE[0] - size[0]) / 2) + x_ofs
            y = ((SCREEN_SIZE[1] - size[1]) / 2) + y_ofs
            self.screen.blit(font_surface, (x, y))

    def get_state(self):
        """ constructs and returns a vector representation of current game state """
        state = {
            'game_state': self.game_state,
            'ball': self.ball,
            'ball_vel': self.ball_vel,
            'boosts_left': self.boosts_remaining,
            'boost_time': self.boost_time,
            'paddle': self.paddle,
            'bricks': self.bricks,
            'time': self.time,
            'score': self.score,
            'lives': self.lives
        }
        return state

    @abc.abstractmethod
    def run(self):
        pass

    def __calc_reward(self, prev, cur):
        """calculates the reward between two states
        """
        if prev == None:
            return 0

        # return +/-1k if game is won/lost, with a little reward for dying closer to the ball
        if prev['game_state'] != STATE_WON and cur['game_state'] == STATE_WON:
            return 1000.0
        elif prev['game_state'] != STATE_GAME_OVER and cur['game_state'] == STATE_GAME_OVER:
            # TODO tune this
            return -(abs(cur['paddle'].x - cur['ball'].x + PADDLE_WIDTH/2 - BALL_RADIUS))*0.05

        # return difference in points, not counting first broken brick
        reward = (cur['score'] - prev['score'])
        if self.hit_ball:
            reward += 5
            self.hit_ball = False
        return reward

    def executeAction(self, action):
        """executes a game turn based on the given action"""
        prev_state = self.get_state()
        self.take_input(action)
        self.execute_turn()
        new_state = self.get_state()
        reward = self.__calc_reward(prev_state, new_state)
        return reward, new_state


class HumanControlledBreakout(Breakout):
    """Breakout subclass which takes inputs from the keyboard during run()
    """

    def __init__(self, csv, verbose, display, batches, write_model, model_path):
        super(HumanControlledBreakout, self).__init__(
            csv, verbose, display, batches, write_model, model_path)

    def _get_input_from_keyboard(self):
        keys = pygame.key.get_pressed()
        input = []
        input += [INPUT_L] if keys[pygame.K_LEFT] else []
        input += [INPUT_R] if keys[pygame.K_RIGHT] else []
        input += [INPUT_B] if keys[pygame.K_b] else []
        input += [INPUT_SPACE] if keys[pygame.K_SPACE] else []
        input += [INPUT_ENTER] if keys[pygame.K_RETURN] else []
        input += [INPUT_QUIT] if keys[pygame.K_q] else []
        return input

    def run(self):
        while 1:
            self.execute_turn()
            self.take_input(self._get_input_from_keyboard())


class BotControlledBreakout(Breakout):
    """Breakout subclass for agent-controlled games.

    Whereas HumanControlledBreakout disregaurds game state, BotControlledBreakout gives a vector representation of
       each state (and possibly other stuff) to a game-playing agent, and recieves input (actions) from this agent
    """

    def __init__(self, agent, csv, verbose, display, batches, write_model, model_path):
        super(BotControlledBreakout, self).__init__(
            csv, verbose, display, batches, write_model, model_path)
        self.agent = agent
        if self.model_path is not None:
            self.agent.read_model(self.model_path)

    def run(self):
        if self.csv:
            print 'cum_score,score,time,bricks'

        cumulative_score = 0
        cumulative_time = 0
        for episode in xrange(self.batches):
            new_action = None
            prev_state = None
            state = self.get_state()
            while state['game_state'] != STATE_GAME_OVER:
                # if newAction is none then we're dealing with an off-policy algorithm:
                #    query the external acting policy for the next action.
                # otherwise, we're training an on-policy algorithm, so take the action
                #    specified by the agent in incorporateFeedback
                if new_action is None:
                    action = self.agent.takeAction(state)
                else:
                    action = new_action
                reward, new_state = self.executeAction(action)
                new_action = self.agent.incorporateFeedback(
                    state, action, reward, new_state)
                state = new_state

            # bookeeping...
            cumulative_score += self.score
            cumulative_time += self.time

            if not self.csv:
                print 'episode %s complete.' % episode
            if self.verbose:
                print 'score,%s|frames,%s|bricks,%s' % (self.score, self.time, len(self.bricks))
            elif self.csv:
                print "%s,%s,%s,%s" % (cumulative_score, self.score, self.time, len(self.bricks))

            self.take_input([INPUT_ENTER])

        if self.write_model is not None:
            self.agent.write_model(self.write_model)

        if self.verbose:
            print '\nFINAL STATS:'
            print 'Performance summary:'
            print '\tGames: %s' % self.batches
            print '\tMean score: %s' % (cumulative_score * 1.0 / self.batches)
            print '\tMean time: %s' % (cumulative_time * 1.0 / self.batches)

        self.take_input([INPUT_QUIT])


class OracleControlledBreakout(Breakout):
    """Breakout subclass for oracle-controlled games.

    The oracle can return any ball - it translates the paddle to 
    match the exact position of the ball at all times
    """

    def __init__(self, csv, verbose, display, batches, write_model):
        super(OracleControlledBreakout, self).__init__(
            csv, verbose, display, batches, write_model)

    def handle_collisions(self):
        """overide super.handle_collisions to give oracle more lenient ball-paddle collision conditions

        accounts for the case where ball velocity is so fast it jumps past the paddle in one game turn
        """
        for brick in self.bricks:
            if self.ball.colliderect(brick):
                self.hit_ball = True
                # only allow points after first brick is broken
                if len(self.bricks) < 6 * 9:
                    self.score += BROKEN_BRICK_PTS
                self.num_hits += 1
                if (brick.x > self.ball.x - self.ball_vel[0] * self.speed_multiplyer + BALL_DIAMETER)\
                        or (brick.x + BRICK_WIDTH < self.ball.x - self.ball_vel[0] * self.speed_multiplyer):
                    self.ball_vel[0] = -self.ball_vel[0]
                else:
                    self.ball_vel[1] = -self.ball_vel[1]
                self.bricks.remove(brick)
                self.speed_multiplyer = min(
                    self.speed_multiplyer + 0.05, MAX_SPEED)
                break

        if len(self.bricks) == 0:
            self.game_state = STATE_WON

        if self.ball.colliderect(self.paddle) or \
                (abs(self.paddle.centerx - self.ball.centerx) < PADDLE_WIDTH * 2 and
                 abs(self.paddle.centery - self.ball.centery) < BALL_DIAMETER):
            distance_from_center = float(
                self.ball.centerx - self.paddle.centerx)
            self.ball.top = PADDLE_Y - BALL_DIAMETER
            self.ball_vel[0] += distance_from_center / 7
            self.ball_vel[1] = -self.ball_vel[1]
        elif self.ball.top > self.paddle.top:
            print self.paddle.centerx, self.paddle.centery
            print self.ball.centerx, self.ball.centery
            self.lives -= 1
            if self.lives > 0:
                self.game_state = STATE_BALL_IN_PADDLE
                self.ball.left = self.paddle.left + self.paddle.width / 2
                self.ball.top = self.paddle.top - self.ball.height
            else:
                self.game_state = STATE_GAME_OVER

    def run(self):
        for episode in range(self.batches):
            while 1:
                self.set_paddle_pos(self.ball.left - 35)
                self.execute_turn()
                if self.game_state == STATE_BALL_IN_PADDLE:
                    self.take_input([INPUT_SPACE])
            self.take_input([INPUT_SPACE])


if __name__ == "__main__":
    HumanControlledBreakout().run()
#    BotControlledBreakout(None, True).run()
