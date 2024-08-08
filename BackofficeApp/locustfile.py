from locust import HttpUser, task, between, TaskSet, SequentialTaskSet
import random, uuid


def token_refresh(User):
    response = User.client.post("/auth/token/refresh/")
    if response.status_code == 200:
        User.client.cookies.set('access_token', response.cookies['access_token'])
        return 200
    return response.status_code


class CoursesSurf(SequentialTaskSet):
    @task
    def list_courses(self):
        response = self.client.get("/api/courses/")
        if response.status_code == 200:
            for i in range(response.json()["count"]):
                self.user.courses_list.append(response.json()["results"][i]["id"])
                
            if response.status_code == 401:
                status_code = token_refresh(self)
                if status_code == 200:
                    self.client.get("/api/courses/")

    @task
    def list_categories(self):
        response = self.client.get("/api/categories/")
        if response.status_code == 401:
            status_code = token_refresh(self)
            if status_code == 200:
                self.client.get("/api/categories/")

    @task
    def list_course(self):
        if len(self.user.courses_list) > 0:
            i = random.choice(self.user.courses_list)
            response = self.client.get("/api/courses/%i/" % i)
            if response.status_code == 401:
                status_code = token_refresh(self)
                if status_code == 200:
                    self.client.get("/api/courses/%i/" % i)

    @task
    def list_lessons(self):
        if len(self.user.courses_list) > 0:
            i = random.choice(self.user.courses_list)
            response = self.client.get("/api/lessons/?course_id=%i" % i)
            if response.status_code == 200:
                for i in range(response.json()["count"]):
                    self.user.lessons_list.append(response.json()["results"][i]["id"])

                if response.status_code == 401:
                    status_code = token_refresh(self)
                    if status_code == 200:
                        self.client.get("/api/lessons/?course_id=%i" % i)

    @task
    def list_lesson(self):
        if len(self.user.lessons_list) > 0:
            i = random.choice(self.user.lessons_list)
            response = self.client.get("/api/lessons/%i/" % i)
            if response.status_code == 401:
                status_code = token_refresh(self)
                if status_code == 200:
                    self.client.get("/api/lessons/%i/" % i)


class EmployeeUser(HttpUser):
    weight = 10
    wait_time = between(5, 10)
    tasks = {CoursesSurf: 10}

    partner_id = 0
    courses_list = []
    lessons_list = []

    def on_start(self):
        response = self.client.post("/api/token/", json={"email": "teacher@gmail.com", "password": "teacher"})
        if response.status_code == 200:
            self.client.cookies.set('access_token', response.cookies['access_token'])
            self.client.cookies.set('refresh_token', response.cookies['refresh_token'])
            self.partner_id = self.client.get("/api/user-group-permissions/").json()["partner_id"]

    @task
    def list_employees(self):
        response = self.client.get("/api/employees/")
        if response.status_code == 401:
            status_code = token_refresh(self)
            if status_code == 200:
                self.client.get("/api/employees/")


class OwnerUser(HttpUser):
    wait_time = between(5, 10)
    weight = 1
    tasks = {CoursesSurf: 7}

    partner_id = 0
    courses_list = []
    lessons_list = []
    branches_list = []
    employees_list = []

    def on_start(self):
        response = self.client.post("/api/token/", json={"email": "owner@gmail.com", "password": "owner"})
        if response.status_code == 200:
            self.client.cookies.set('access_token', response.cookies['access_token'])
            self.client.cookies.set('refresh_token', response.cookies['refresh_token'])
            self.partner_id = self.client.get("/api/user-group-permissions/").json()["partner_id"]

    @task(10)
    def list_partner(self):
        response = self.client.get("/api/partners/%i/" % self.partner_id)
        if response.status_code == 401:
            status_code = token_refresh(self)
            if status_code == 200:
                self.client.get("/api/partners/")

    @task(100)
    def change_partner(self):
        response = self.client.patch("/api/partners/%i/" % self.partner_id, data={})
        if response.status_code == 401:
            status_code = token_refresh(self)
            if status_code == 200:
                self.client.get("/api/partners/")

    @task(3)
    def list_branches(self):
        response = self.client.get("/api/branches/")
        if response.status_code == 200:
            for i in range(response.json()["count"]):
                self.branches_list.append(response.json()["results"][i]["id"])

            if response.status_code == 401:
                status_code = token_refresh(self)
                if status_code == 200:
                    self.client.get("/api/branches/")


    @task
    def change_branch(self):
        if len(self.branches_list) > 0:
            i = random.choice(self.branches_list)
            response = self.client.patch("/api/branches/%i/" % i, data={})
            if response.status_code == 401:
                status_code = token_refresh(self)
                if status_code == 200:
                    self.client.get("/api/branches/")

    @task(4)
    def list_employees(self):
        response = self.client.get("/api/employees/")
        if response.status_code == 200:
            for i in range(response.json()["count"]):
                self.employees_list.append(response.json()["results"][i]["user"]["id"])

            if response.status_code == 401:
                status_code = token_refresh(self)
                if status_code == 200:
                    self.client.get("/api/employees/")

    @task(8)
    def list_employee(self):
        if len(self.employees_list) > 0:
            i = random.choice(self.employees_list)
            response = self.client.get("/api/employees/%i/" % i)
            if response.status_code == 401:
                status_code = token_refresh(self)
                if status_code == 200:
                    self.client.get("/api/employees/%i/" % i)

    @task
    def change_employee(self):
        if len(self.employees_list) > 0:
            i = random.choice(self.employees_list)
            response = self.client.patch("/api/employees/%i/" % i, data={})
            if response.status_code == 401:
                status_code = token_refresh(self)
                if status_code == 200:
                    self.client.get("/api/employees/")


class Superuser(HttpUser):
    fixed_count = 1
    tasks = {CoursesSurf: 10}

    partner_list = []
    courses_list = []
    lessons_list = []
    branches_list = []
    employees_list = []

    def on_start(self):
        response = self.client.post("/api/token/", json={"email": "superuser@gmail.com", "password": "superuser"})
        if response.status_code == 200:
            self.client.cookies.set('access_token', response.cookies['access_token'])
            self.client.cookies.set('refresh_token', response.cookies['refresh_token'])
            self.client.get("/api/user-group-permissions/")

    @task
    def change_course(self):
        if len(self.courses_list) > 0:
            i = random.choice(self.courses_list)
            response = self.client.patch("/api/courses/%i/" % i, data={})
            if response.status_code == 401:
                status_code = token_refresh(self)
                if status_code == 200:
                    self.client.get("/api/courses/")

    @task
    def change_lesson(self):
        if len(self.lessons_list) > 0:
            i = random.choice(self.lessons_list)
            response = self.client.patch("/api/lessons/%i/" % i, data={})
            if response.status_code == 401:
                status_code = token_refresh(self)
                if status_code == 200:
                    self.client.get("/api/lessons/")

    @task(12)
    def list_partners(self):
        response = self.client.get("/api/partners/")
        if response.status_code == 200:
            for i in range(response.json()["count"]):
                self.partner_list.append(response.json()["results"][i]["id"])

            if response.status_code == 401:
                status_code = token_refresh(self)
                if status_code == 200:
                    self.client.get("/api/partners/")

    @task(10)
    def list_partner(self):
        if len(self.partner_list) > 0:
            i = random.choice(self.partner_list)
            response = self.client.get("/api/partners/%i/" % i)
            if response.status_code == 401:
                status_code = token_refresh(self)
                if status_code == 200:
                    self.client.get("/api/partners/")

    @task
    def change_partner(self):
        if len(self.partner_list) > 0:
            i = random.choice(self.partner_list)
            response = self.client.patch("/api/partners/%i/" % i, data={})
            if response.status_code == 401:
                status_code = token_refresh(self)
                if status_code == 200:
                    self.client.get("/api/partners/")

    @task(3)
    def list_branches(self):
        response = self.client.get("/api/branches/")
        if response.status_code == 200:
            for i in range(response.json()["count"]):
                self.branches_list.append(response.json()["results"][i]["id"])

            if response.status_code == 401:
                status_code = token_refresh(self)
                if status_code == 200:
                    self.client.get("/api/branches/")


    @task
    def change_branch(self):
        if len(self.branches_list) > 0:
            i = random.choice(self.branches_list)
            response = self.client.patch("/api/branches/%i/" % i, data={})
            if response.status_code == 401:
                status_code = token_refresh(self)
                if status_code == 200:
                    self.client.get("/api/branches/")

    @task(4)
    def list_employees(self):
        response = self.client.get("/api/employees/")
        if response.status_code == 200:
            for i in range(response.json()["count"]):
                self.employees_list.append(response.json()["results"][i]["user"]["id"])

            if response.status_code == 401:
                status_code = token_refresh(self)
                if status_code == 200:
                    self.client.get("/api/employees/")

    @task(8)
    def list_employee(self):
        if len(self.employees_list) > 0:
            i = random.choice(self.employees_list)
            response = self.client.get("/api/employees/%i/" % i)
            if response.status_code == 401:
                status_code = token_refresh(self)
                if status_code == 200:
                    self.client.get("/api/employees/%i/" % i)

    @task
    def change_employee(self):
        if len(self.employees_list) > 0:
            i = random.choice(self.employees_list)
            response = self.client.patch("/api/employees/%i/" % i, data={})
            if response.status_code == 401:
                status_code = token_refresh(self)
                if status_code == 200:
                    self.client.get("/api/employees/")
