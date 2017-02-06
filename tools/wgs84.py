from math import sqrt, cos, sin, pi as PI


class Point2D:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def getY(self):
        return self.y

    def getX(self):
        return self.x


class WGS84Coordinate:
    """
    Constructor.

    @param lat Latitude (positive is north, negative is south).
    @param lon Longitude (negative is west, positive is east).
    """

    def __init__(self, lat, lon):
        self.EQUATOR_RADIUS = 6378137.0
        self.FLATTENING = 1.0 / 298.257223563
        self.SQUARED_ECCENTRICITY = 2.0 * self.FLATTENING - self.FLATTENING * self.FLATTENING
        self.POLE_RADIUS = self.EQUATOR_RADIUS * sqrt(1.0 - self.SQUARED_ECCENTRICITY)
        self.C00 = 1.0
        self.C02 = 0.25
        self.C04 = 0.046875
        self.C06 = 0.01953125
        self.C08 = 0.01068115234375
        self.C22 = 0.75
        self.C44 = 0.46875
        self.C46 = 0.01302083333333333333
        self.C48 = 0.00712076822916666666
        self.C66 = 0.36458333333333333333
        self.C68 = 0.00569661458333333333
        self.C88 = 0.3076171875

        self.R0 = self.C00 - self.SQUARED_ECCENTRICITY * (
        self.C02 + self.SQUARED_ECCENTRICITY * (self.C04 + self.SQUARED_ECCENTRICITY * (self.C06 + self.SQUARED_ECCENTRICITY * self.C08)))
        self.R1 = self.SQUARED_ECCENTRICITY * (
        self.C22 - self.SQUARED_ECCENTRICITY * (self.C04 + self.SQUARED_ECCENTRICITY * (self.C06 + self.SQUARED_ECCENTRICITY * self.C08)))
        self.R2T = self.SQUARED_ECCENTRICITY * self.SQUARED_ECCENTRICITY
        self.R2 = self.R2T * (self.C44 - self.SQUARED_ECCENTRICITY * (self.C46 + self.SQUARED_ECCENTRICITY * self.C48))
        self.R3T = self.R2T * self.SQUARED_ECCENTRICITY
        self.R3 = self.R3T * (self.C66 - self.SQUARED_ECCENTRICITY * self.C68)
        self.R4 = self.R3T * self.SQUARED_ECCENTRICITY * self.C88

        # These members are used in projective computations.
        self.m_latitude = 0
        self.m_longitude = 0
        self.m_ml0 = 0
        self.deg2rad = PI / 180.0

        self.lat = lat
        self.lon = lon
        self.initialize()

    def getLongitude(self):
        return self.lon

    def getLatitude(self):
        return self.lat

    def transformToCart(self, lat, lon):
        result = self.fwd(lat * self.deg2rad, lon * self.deg2rad)
        return result

    def transformToWGS84XY(self, x, y):
        coordinate = Point2D(x, y)
        return self.transform(coordinate, 1e-2)

    def transformToWGS84(self, coordinate):
        return self.transform(coordinate, 1e-2)

    def transformToWGS84(self, coordinate, accuracy):
        result = WGS84Coordinate(self.getLatitude(), self.getLongitude())
        addLon = 1e-5
        signLon = -1 if (coordinate.getX() < 0) else 1
        addLat = 1e-5

        signLat = -1 if (coordinate.getY() < 0) else 1

        epsilon = accuracy
        if (epsilon < 0):
            epsilon = 1e-2

        point3Result = self.transform(result)
        dOld = float("inf")
        d = abs(coordinate.getY() - point3Result.getY())
        iterations = 0

        # while ((d < dOld) & & (d > epsilon) & & (iterations < 50000)) {
        while (d < dOld) and (d > epsilon):
            result = WGS84Coordinate(result.m_latitude + signLat * addLat, result.getLatitude())
            point3Result = self.transform(result)
            dOld = d
            d = abs(coordinate.getY() - point3Result.getY())
            iterations += 1

        # Use the last transformed point3Result here.
        dOld = float("inf")
        d = abs(coordinate.getX() - point3Result.getX())
        iterations = 0

        # while ((d < dOld) & & (d > epsilon) & & (iterations < 50000)) {
        while (d < dOld) and (d > epsilon):
            result = WGS84Coordinate(result.m_latitude, result.getLongitude() + signLon * addLon)
            point3Result = self.transform(result)
            dOld = d
            d = abs(coordinate.getX() - point3Result.getX())
            iterations += 1
        return result

    def initialize(self):
        self.m_latitude = self.getLatitude() * self.deg2rad
        self.m_longitude = self.getLongitude() * self.deg2rad
        self.m_ml0 = self.mlfn(self.m_latitude)

    def mlfn(self, lat):
        sin_phi = sin(lat)
        cos_phi = cos(lat)
        cos_phi *= sin_phi
        sin_phi *= sin_phi

        return self.R0 * lat - cos_phi * (self.R1 + sin_phi * (self.R2 + sin_phi * (self.R3 + sin_phi * self.R4)))

    def msfn(self, sinPhi, cosPhi, es):
        return cosPhi / sqrt(1.0 - es * sinPhi * sinPhi)

    def fwd(self, lat, lon):
        result = [0, 0]

        t = abs(lat) - PI / 2.0

        if (t > 1.0e-12) or (abs(lon) > 10.0):
            return result

        if abs(t) < 1.0e-12:
            if lat < 0.0:
                lat = -PI / 2.0
            else:
                lat = PI / 2.0

        lon -= self.m_longitude

        projectiveResult = self.project(lat, lon)
        result[0] = self.EQUATOR_RADIUS * projectiveResult[0]
        result[1] = self.EQUATOR_RADIUS * projectiveResult[1]

        return result

    def project(self, lat, lon):
        result = [0, 0]

        if abs(lat) < 1e-10:
            result[0] = lon
            result[1] = -self.m_ml0
        else:
            if abs(sin(lat)) > 1e-10:
                ms = self.msfn(sin(lat), cos(lat), self.SQUARED_ECCENTRICITY) / sin(lat)
            else:
                ms = 0.0
            lon *= sin(lat)
            result[0] = ms * sin(lon)
            result[1] = (self.mlfn(lat) - self.m_ml0) + ms * (1.0 - cos(lon))

        return result
