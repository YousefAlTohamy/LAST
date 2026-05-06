import math

class KinematicsCalculator:
    """
    Independent module for all biomechanical mathematical calculations.
    Ensures separation of concerns from UI and Video Processing.
    """

    @staticmethod
    def calculate_angle(a, b, c):
        """
        Calculates the interior angle at point 'b' given three points a, b, c.
        Points are tuples of (x, y) coordinates.
        Returns the angle in degrees between 0 and 180.
        """
        if not (a and b and c):
            return 0.0

        # math.atan2(y, x) computes the angle counter-clockwise from the x-axis
        radians = math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
        angle = math.degrees(radians)
        
        # We only care about the absolute interior angle
        angle = abs(angle)
        if angle > 180.0:
            angle = 360.0 - angle
            
        return angle

    @staticmethod
    def calculate_elevation_angle(hip, ankle):
        """
        Calculates the elevation angle of the leg relative to a horizontal reference line.
        Assumes the camera is viewing the patient from the side.
        """
        if not (hip and ankle):
            return 0.0

        # Calculate absolute horizontal distance
        dx = abs(ankle[0] - hip[0])
        
        # Calculate vertical distance (Y increases downwards in OpenCV)
        # We want positive dy when ankle is higher (closer to top of screen) than hip
        dy = hip[1] - ankle[1] 
        
        # Calculate angle and convert to degrees
        angle = math.degrees(math.atan2(dy, dx))
        
        return angle
