import RPi.GPIO as GPIO
import time


def buzz():
    GPIO.setmode(GPIO.BCM)

    # Setup GPIO Pins
    GPIO.setup(40, GPIO.OUT)
    # Set PWM instance and their frequency
    pwm12 = GPIO.PWM(40, 5000)
    # pwm12.stop()

    # Start PWM with 50% Duty Cycle
    pwm12.start(50)
    time.sleep(1)

    pwm12.stop()

    # Cleans the GPIO
    GPIO.cleanup()


if __name__ == '__main__':
    buzz()
