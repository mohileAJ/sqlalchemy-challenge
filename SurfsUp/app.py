# Import the dependencies.
import numpy as np
import pandas as pd
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################


# reflect an existing database into a new model
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
@app.get("/")
def homepage():
  """List all available api routes."""

  return (
    f"Available Routes: <br/>"
    f"/api/v1.0/precipitation <br/>"
    f"/api/v1.0/stations <br/>"
    f"/api/v1.0/tobs <br/>"
    f"/api/v1.0/<start> <br/>"
    f"/api/v1.0/<start>/<end> <br/>"
  )

# Return the last full year of precipitation data, in json format
@app.get("/api/v1.0/precipitation")
def get_precipitation():
  # Date of the most recent measuremnt
  most_recent_date, = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
  # One-year before the most recent measurement date
  one_year_ago = (dt.datetime.strptime(most_recent_date, '%Y-%m-%d') - dt.timedelta(days=365)).strftime('%Y-%m-%d')

  # Perform a query to retrieve the data and precipitation scores
  results = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= one_year_ago).all()

  results_json = {}
  for date, precip in results:
    if date in results_json:
      results_json[date].append(precip)
    else:
      results_json[date] = [precip]
  
  return jsonify(results_json)


@app.get("/api/v1.0/stations")
def get_stations():
  # Return a list of stations from the dataset
  stations = session.query(Station.id, Station.station, Station.name, Station.latitude, Station.longitude, Station.elevation).all()
  
  stations_json = []
  for id, station, name, latitude, longitude, elevation in stations:
    stations_json.append({
      "id": id,
      "station": station,
      "name": name,
      "latitude": latitude,
      "longitude": longitude,
      "elevation": elevation
    })

  return jsonify(stations_json)

@app.get("/api/v1.0/tobs")
def get_most_active_station_temps_last_year():
  # Compute 1 year ago cutoff
  most_recent_date, = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
  one_year_ago = (dt.datetime.strptime(most_recent_date, '%Y-%m-%d') - dt.timedelta(days=365)).strftime('%Y-%m-%d')

  # Compute most active station
  most_active_station, = session.query(func.max(Measurement.station)).filter(Measurement.date >= one_year_ago).first()

  # Perform a query to retrieve the data and precipitation scores
  results = session.query(Measurement.date, Measurement.tobs).filter(Measurement.station == most_active_station).filter(Measurement.date >= one_year_ago).all()

  # Constructing the response dictionary
  results_json = []
  for date, tobs in results:
    results_json.append({
      "date": date,
      "tobs": tobs
    })
  
  return jsonify(results_json)

@app.get("/api/v1.0/<start>")
@app.get("/api/v1.0/<start>/<end>")
def get_temps_for_dates(start, end=None):
  # Perform a query with start date.
  query = session.query(
    Measurement.date,
    func.min(Measurement.tobs),
    func.avg(Measurement.tobs),
    func.max(Measurement.tobs)
  ).group_by(Measurement.date)
  
  query = query.filter(Measurement.date >= start)
  if end is not None:
    query = query.filter(Measurement.date <= end)
  
  results = query.all()

  results_json = []
  for date, tmin, tmax, tavg in results:
    results_json.append({
      "date": date,
      "TMIN": tmin,
      "TMAX": tmax,
      "TAVG": tavg
    })
  
  return jsonify(results_json)

if __name__ == "__main__":
  app.run(debug=True)