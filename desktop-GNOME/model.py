# coding: utf-8

from pymongo import MongoClient
from datetime import datetime


class Model:
    def __init__(self):
        self.client = MongoClient('localhost', 27017)
        self.db = self.client.workouts

    def get_workout_list(self):
        result = []
        for workout in self.db.workouts.find():
            result.append(Workout.from_data(workout))
        return result

    def get_steps_of(self, workout_name):
        result = []
        workout_data = self.db.workouts.find_one({'name': workout_name})
        exercise_list = workout_data.get('exercises')
        for exercise in exercise_list:
            if exercise[0] == 'rest':
                result.append(Rest(exercise[1]))
            else:
                query = self.db.exercises.find_one({'name': exercise[0]})
                if query is not None:
                    result.append(Exercise.from_data(query, exercise[1]))
                else:
                    result.append(
                        Exercise(exercise[0], None, None, None, exercise[1]))
        return result

    def delete_workout(self, workout_name):
        self.db.workouts.find_one_and_delete({'name': workout_name})


class Workout:
    def __init__(self, name, image, date):
        # thanks to the possibillity of using @Property later without
        # changing the caller, we can leave these attributes as public
        self.name = name
        self.image = image
        self.date = date

    @classmethod
    def from_data(cls, data):
        retrieved_date = data.get('date')
        if retrieved_date == None:
            date = None
        else:
            date = datetime.strptime(retrieved_date, '%d-%m-%Y')
        return Workout(data.get('name'), data.get('image'), date)


class WorkoutStep:
    def __init__(self, step_type, duration):
        self.step_type = step_type
        self.duration = duration


class Rest(WorkoutStep):
    def __init__(self, duration):
        super().__init__('Rest', duration)


class Exercise(WorkoutStep):
    def __init__(self, name, image, description, video, duration):
        super().__init__('Exercise', duration)
        self.name = name
        self.image = image
        self.description = description
        self.video = video

    @staticmethod
    def from_data(data, duration):
        description = data.get('description')
        if description != '':
            description_string = ''
            for line in data.get('description'):
                description_string = description_string + line + '\n'
            # Remove the trailing newline
            description_string = description_string[0:len(
                description_string)-1]
        else:
            description_string = None
        return Exercise(data.get('name'), data.get('image'),
                        description_string, data.get('video'), duration)
