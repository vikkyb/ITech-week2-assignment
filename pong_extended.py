import sys
import pygame
import random
import numpy as np


class Paddle(pygame.Rect):
    def __init__(self, velocity, up_key, down_key, left_key, right_key, *args, **kwargs):
        self.velocity = velocity
        self.up_key = up_key
        self.down_key = down_key
        self.left_key = left_key
        self.right_key = right_key
        super().__init__(*args, **kwargs)

    def move_paddle(self, board_height, board_width):
        keys_pressed = pygame.key.get_pressed()

        if keys_pressed[self.up_key]:
            if self.y - self.velocity > 0:
                self.y -= self.velocity

        if keys_pressed[self.down_key]:
            if self.y + self.velocity < board_height - self.height:
                self.y += self.velocity

        if keys_pressed[self.left_key]:
            if self.x + self.velocity > 0:
                self.x -= self.velocity

        if keys_pressed[self.right_key]:
            if self.x + self.velocity < board_width - self.width:
                self.x += self.velocity


class Ball(pygame.Rect):
    def __init__(self, velocity, *args, **kwargs):
        self.velocity = velocity
        self.angle = 0
        super().__init__(*args, **kwargs)

    def move_ball(self):
        self.x += self.velocity
        self.y += round(self.angle)

    def change_velocity_ball(self, multiplier):
        self.velocity = self.velocity * multiplier


class Bar(pygame.Rect):
    def __init__(self, velocity, *args, **kwargs):
        self.velocity = velocity
        self.angle = 1
        super().__init__(*args, **kwargs)

    def move_bar(self):
        self.x += self.angle * self.velocity


class Pong:
    BPM = 120       # Beats per minute
    BPS = BPM/60
    BPF = BPS/60
    FPB = 1/BPF
    good_timing = [27, 28, 29, 30, 0, 1, 2, 3, 12, 13, 14, 15, 16, 17, 18] # Frame which are counted as good
    frame = -2
    
    HEIGHT = 600
    WIDTH = 1200

    PADDLE_WIDTH = 50
    PADDLE_HEIGHT = 50
    PADDLE_VELOCITY = 8
    BALL_WIDTH = 10
    BALL_VELOCITY = 5
    BALL_ANGLE = 0

    BAR_SPEED = 5
    BAR_X = 0

    CIRCLE_SPEED = 2
    CIRCLE_MAX_SIZE = 70
    CIRCLE_MIN_SIZE = 50
    CIRCLE_SPEED_UP = 1.5  # Change in speed when pressing space; speed = CIRCLE_SPEED_UP * speed

    COLOUR = (255, 255, 255)

    FADE = 10  # Adjust to change fade out speed, higher is faster
    RATIO_GOOD = 4  # RATIO_GOOD times more likely to pass a good ball than a bad ball

    def __init__(self):
        pygame.init()  # Start the pygame instance.

        # Setup the screen
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.clock = pygame.time.Clock()

        # Setup the field
        self.central_line = pygame.Rect(self.WIDTH / 2, 0, 5, self.HEIGHT)
        self.left_third_line = pygame.Rect(self.WIDTH / 3, 0, 3, self.HEIGHT)
        self.right_third_line = pygame.Rect(2 * self.WIDTH / 3, 0, 3, self.HEIGHT)
        self.left_line = pygame.Rect(0, 0, 5, self.HEIGHT)
        self.right_line = pygame.Rect(self.WIDTH - 5, 0, 5, self.HEIGHT)
        self.top_line = pygame.Rect(0, self.HEIGHT - 5, self.WIDTH, 5)
        self.bottom_line = pygame.Rect(0, 0, self.WIDTH, 5)

        # Pointers around players
        self.circle_size = self.CIRCLE_MIN_SIZE
        self.circle_direction = 1

        # Create the player objects.
        self.paddles = []
        self.balls = []
        self.paddles.append(Paddle(  # The left paddle
            self.PADDLE_VELOCITY,
            pygame.K_w,
            pygame.K_s,
            pygame.K_a,
            pygame.K_d,
            100,
            self.HEIGHT / 2 - self.PADDLE_HEIGHT / 2,
            self.PADDLE_WIDTH,
            self.PADDLE_HEIGHT
        ))

        self.paddles.append(Paddle(  # The right paddle
            self.PADDLE_VELOCITY,
            pygame.K_UP,
            pygame.K_DOWN,
            pygame.K_LEFT,
            pygame.K_RIGHT,

            self.WIDTH - self.PADDLE_WIDTH - 100,
            self.HEIGHT / 2 - self.PADDLE_HEIGHT / 2,
            self.PADDLE_WIDTH,
            self.PADDLE_HEIGHT
        ))

        self.balls.append(Ball(
            self.BALL_VELOCITY,
            self.WIDTH / 2 - self.BALL_WIDTH / 2,
            self.HEIGHT / 2 - self.BALL_WIDTH / 2,
            self.BALL_WIDTH,
            self.BALL_WIDTH
        ))

        # For lighting up right side of the field
        self.light_up_right = 0
        self.light_up_colour_right = (255, 255, 255)
        self.fade_colour_right = (self.FADE, self.FADE, self.FADE)
        self.light_up_rect_right = pygame.Rect(self.WIDTH / 2, 0, self.WIDTH / 2, self.HEIGHT)

        # For lighting up left side of the field
        self.light_up_left = 0
        self.light_up_colour_left = (255, 0, 0)
        self.fade_colour_left = (self.FADE, 0, 0)
        self.light_up_rect_left = pygame.Rect(0, 0, self.WIDTH / 2, self.HEIGHT)

        # Keys for adjusting speed, helps to only apply once, not continuously
        self.space_pressed = False
        self.c_pressed = False

        # Text speed
        self.speed_font = pygame.font.SysFont('Yu Gothic UI Semibold', 250)
        self.speed_text_surface_left = self.speed_font.render('78', False, (255, 255, 255))
        self.speed_text_surface_left = pygame.transform.rotate(self.speed_text_surface_left, 90)
        (self.width_speed_text, self.height_speed_text) = self.speed_text_surface_left.get_size()

        self.speed_text_surface_right = self.speed_font.render('75', False, (255, 255, 255))
        self.speed_text_surface_right = pygame.transform.rotate(self.speed_text_surface_right, -90)

        self.speed_multiplier_for_text = 1

    def check_ball_hits_wall(self):
        for ball in self.balls:
            if ball.x > self.WIDTH or ball.x < 0:
                sys.exit(1)

            if ball.y > self.HEIGHT - self.BALL_WIDTH or ball.y < 0:
                sys.exit(1)
                # ball.angle = -ball.angle

    def check_ball_hits_paddle(self):
        for ball in self.balls:
            for paddle in self.paddles:
                if ball.colliderect(paddle):
                    ball.velocity = -ball.velocity
                    ball.x += ball.velocity * 10
                    paddle.x -= ball.velocity * 10
                    ball.angle = (((self.HEIGHT / 2 - ball.y) / (self.HEIGHT / 2)) + (np.random.random() - 0.5)) * abs(
                        ball.velocity)

                    if round(self.frame % self.FPB) in self.good_timing:
                        if ball.x > self.WIDTH / 2 and not self.light_up_right:
                            self.start_light_up_right(True)
                            self.update_speed_left()
                        elif not self.light_up_left:
                            self.start_light_up_left(True)
                            self.update_speed_right()
                        break
                    else:
                        if ball.x > self.WIDTH / 2 and not self.light_up_right:
                            self.start_light_up_right(False)
                            self.update_speed_left()
                        elif not self.light_up_left:
                            self.start_light_up_left(False)
                            self.update_speed_right()
                        break


    # Start to light up right side of the field
    def start_light_up_right(self, good):
        self.light_up_right = 1
        if good:
            self.light_up_colour_right = (255, 255, 255)
            self.fade_colour_right = (self.FADE, self.FADE, self.FADE)
        else:
            self.light_up_colour_right = (255, 0, 0)
            self.fade_colour_right = (self.FADE, 0, 0)


    # Start to light up left side of the field
    def start_light_up_left(self, good):
        self.light_up_left = 1
        if good:
            self.light_up_colour_left = (255, 255, 255)
            self.fade_colour_left = (self.FADE, self.FADE, self.FADE)
        else:
            self.light_up_colour_left = (255, 0, 0)
            self.fade_colour_left = (self.FADE, 0, 0)


    # Update lit up sides of the field
    def adjust_light_up(self):
        if self.light_up_right:
            self.light_up_colour_right = \
                tuple(x1 - x2 for x1, x2 in zip(self.light_up_colour_right, self.fade_colour_right))
            if self.light_up_colour_right[0] < 0:
                self.light_up_right = 0
            return False
        if self.light_up_left:
            self.light_up_colour_left = \
                tuple(x1 - x2 for x1, x2 in zip(self.light_up_colour_left, self.fade_colour_left))
            if self.light_up_colour_left[0] < 0:
                self.light_up_left = 0
            return False


    def update_speed_left(self):
        speed = int(random.randint(70, 85) * self.speed_multiplier_for_text)
        self.speed_text_surface_left = self.speed_font.render(str(speed), False, (255, 255, 255))
        self.speed_text_surface_left = pygame.transform.rotate(self.speed_text_surface_left, 90)


    def update_speed_right(self):
        speed = int(random.randint(70, 85) * self.speed_multiplier_for_text)
        self.speed_text_surface_right = self.speed_font.render(str(speed), False, (255, 255, 255))
        self.speed_text_surface_right = pygame.transform.rotate(self.speed_text_surface_right, 90)


    def game_loop(self):
        pygame.mixer.music.load("Epoch.mp3")
        pygame.mixer.music.play()
        while True:

            for event in pygame.event.get():
                # Add some extra ways to exit the game.
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return
            self.check_ball_hits_paddle()

            self.check_ball_hits_wall()

            # Redraw the screen
            self.screen.fill((0, 0, 0))

            # Update lit up sides
            self.adjust_light_up()
            if self.light_up_right:
                pygame.draw.rect(self.screen, self.light_up_colour_right, self.light_up_rect_right)
            if self.light_up_left:
                pygame.draw.rect(self.screen, self.light_up_colour_left, self.light_up_rect_left)

            # Draw field
            pygame.draw.rect(self.screen, self.COLOUR, self.central_line)
            pygame.draw.rect(self.screen, self.COLOUR, self.left_third_line)
            pygame.draw.rect(self.screen, self.COLOUR, self.right_third_line)
            pygame.draw.rect(self.screen, self.COLOUR, self.left_line)
            pygame.draw.rect(self.screen, self.COLOUR, self.right_line)
            pygame.draw.rect(self.screen, self.COLOUR, self.top_line)
            pygame.draw.rect(self.screen, self.COLOUR, self.bottom_line)

            # Project text
            (self.width_speed_text_l, self.height_speed_text_l) = self.speed_text_surface_left.get_size()
            (self.width_speed_text_r, self.height_speed_text_r) = self.speed_text_surface_right.get_size()
            self.screen.blit(self.speed_text_surface_left, (self.WIDTH / 6 - self.width_speed_text_l / 2,
                                                            self.HEIGHT / 2 - self.height_speed_text_l / 2))
            self.screen.blit(self.speed_text_surface_right, (5 * self.WIDTH / 6 - self.width_speed_text_r / 2,
                                                             self.HEIGHT / 2 - self.height_speed_text_r / 2))

            # Control circle speed
            if not self.space_pressed and pygame.key.get_pressed()[pygame.K_SPACE]:
                self.CIRCLE_SPEED = self.CIRCLE_SPEED * self.CIRCLE_SPEED_UP
                for ball in self.balls:
                    ball.change_velocity_ball(self.CIRCLE_SPEED_UP)
                self.speed_multiplier_for_text = self.speed_multiplier_for_text * self.CIRCLE_SPEED_UP
                self.space_pressed = True
            elif self.space_pressed and not pygame.key.get_pressed()[pygame.K_SPACE]:
                self.space_pressed = False

            if not self.c_pressed and pygame.key.get_pressed()[pygame.K_c]:
                self.CIRCLE_SPEED = self.CIRCLE_SPEED / self.CIRCLE_SPEED_UP
                for ball in self.balls:
                    ball.change_velocity_ball(1 / self.CIRCLE_SPEED_UP)
                self.speed_multiplier_for_text = self.speed_multiplier_for_text / self.CIRCLE_SPEED_UP
                self.c_pressed = True
            elif self.c_pressed and not pygame.key.get_pressed()[pygame.K_c]:
                self.c_pressed = False

            # Determine new size circle around player
            if self.circle_size < self.CIRCLE_MIN_SIZE or self.circle_size > self.CIRCLE_MAX_SIZE:
                self.circle_direction = -self.circle_direction
            self.circle_size += self.circle_direction * self.CIRCLE_SPEED

            for paddle in self.paddles:
                # Draw circles around players
                pygame.draw.circle(self.screen, (26, 235, 235),
                                   (paddle.x + int(0.5 * self.PADDLE_WIDTH), paddle.y + int(0.5 * self.PADDLE_WIDTH)),
                                   40)
                pygame.draw.circle(self.screen, (26, 235, 235),
                                   (paddle.x + int(0.5 * self.PADDLE_WIDTH), paddle.y + int(0.5 * self.PADDLE_WIDTH)),
                                   int(self.circle_size), 8)

                # Update and draw players
                paddle.move_paddle(self.HEIGHT, self.WIDTH)
                pygame.draw.rect(self.screen, self.COLOUR, paddle)

            # We know we're not ending the game so lets move the ball here.
            for ball in self.balls:
                ball.move_ball()
                pygame.draw.rect(self.screen, self.COLOUR, ball)

            self.frame += 1

            pygame.display.flip()
            self.clock.tick(60)


if __name__ == '__main__':
    pong = Pong()
    pong.game_loop()
