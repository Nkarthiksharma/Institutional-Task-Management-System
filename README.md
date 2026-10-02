# Institutional Task Management System

A web-based **Institutional Task Management System** developed for managing, assigning, tracking, and monitoring academic and administrative tasks within an educational institution.

The system provides different levels of access for **Institutional Leadership, HODs, and Faculty**, allowing tasks to be created, assigned, updated, monitored, and reviewed in a structured manner.

## Features

* **Role-Based Login**

  * Principal
  * Vice-Principal
  * Deans
  * HOD
  * Faculty

* **Task Management**

  * Create institutional tasks
  * Assign tasks to responsible faculty or departments
  * Set due dates
  * Add task details and instructions
  * Update task status and details

* **Department-Based Management**

  * HODs can manage tasks related to their department
  * Faculty can view and work on assigned tasks
  * Institutional Leadership can monitor institution-level tasks

* **Task Communication**

  * Faculty can communicate regarding tasks
  * Previous messages related to a task can be viewed

* **Task Monitoring**

  * Track task details and deadlines
  * Monitor task progress
  * Maintain task-related records

* **Audit / History**

  * Maintains historical records of task changes
  * Helps track updates made to institutional tasks

* **Email Support**

  * Flask-Mail integration for sending system emails/notifications

## User Roles

### Institutional Leadership

The following roles operate at the institutional leadership level:

* Principal
* Vice-Principal
* Deans

They can:

* Create institutional-level tasks
* Assign tasks to departments or responsible personnel
* Monitor institutional tasks
* View task-related information
* Track task progress and deadlines
* Review task updates

### HOD

The HOD manages tasks within their department and can:

* Create department-level tasks
* Assign tasks to faculty
* Monitor departmental tasks
* Update relevant tasks
* Communicate regarding tasks

### Faculty

Faculty members can:

* View assigned tasks
* View task details
* Work on assigned tasks
* Provide task-related updates
* Communicate regarding tasks

## Technology Stack

### Frontend

* HTML5
* CSS3
* JavaScript
* Bootstrap / Custom CSS

### Backend

* Python
* Flask
* Flask-WTF
* Flask-Mail

### Database

* MySQL
* PyMySQL

### Other Technologies

* CKEditor
* Select2
* Jinja2
* Git & GitHub

## System Architecture

```text
              ┌─────────────────────────────────┐
              │      Institutional Leadership    │
              │                                 │
              │   Principal | Vice-Principal    │
              │             | Deans             │
              └────────────────┬────────────────┘
                               │
                               ▼
              ┌─────────────────────────────────┐
              │              HODs               │
              │       Department Management     │
              └────────────────┬────────────────┘
                               │
                               ▼
              ┌─────────────────────────────────┐
              │             Faculty             │
              │        Assigned Tasks           │
              └────────────────┬────────────────┘
                               │
                               ▼
              ┌─────────────────────────────────┐
              │          Flask Web App          │
              │                                 │
              │ Authentication                  │
              │ Task Management                 │
              │ Role-Based Access               │
              │ Communication                   │
              │ Audit / History                 │
              └────────────────┬────────────────┘
                               │
                               ▼
              ┌─────────────────────────────────┐
              │             MySQL               │
              │                                 │
              │ User Data                       │
              │ Task Data                       │
              │ Task History                    │
              │ Related Records                 │
              └─────────────────────────────────┘
```

## Role-Based Access Control

The system uses role-based access control according to the responsibilities of each user.

```text
              Institutional Leadership
           ┌────────────┬────────────┐
           │            │            │
       Principal   Vice-Principal   Deans
           │            │            │
           └────────────┴────────────┘
                        │
                        ▼
                       HOD
                        │
                        ▼
                     Faculty
```

The **Principal, Vice-Principal, and Deans are institutional-level roles**, while the **HOD manages department-level activities** and Faculty members work on assigned tasks.

Access to tasks and operations is determined based on the user's role and, where applicable, department.

## Task Workflow

```text
Create Task
     │
     ▼
Assign Task
     │
     ▼
Responsible Department / Faculty
     │
     ▼
Task Work / Updates
     │
     ▼
Task Monitoring
     │
     ▼
Completion / Review
```

## Database

The system uses **MySQL** for storing application data.

Important data includes:

* Faculty/user information
* Departments
* Tasks
* Task details
* Due dates
* Task creators
* Task history
* Task-related communication

The system also maintains historical information so that changes to tasks can be tracked.

## Project Structure

A simplified structure of the project is:

```text
CollegeProject/
│
├── app.py / main.py
├── templates/
│   ├── login.html
│   ├── dashboard.html
│   ├── tasks.html
│   ├── task_details.html
│   └── ...
├── requirements.txt
├── README.md
└── ...
```

> The exact filenames and folders may vary depending on the current version of the project.

## Security

The project uses role-based access control to restrict functionality according to the user's role.

For deployment:

* Store database credentials in environment variables.
* Do not commit passwords or secret keys.
* Use secure session configuration.
* Use HTTPS when deploying publicly.
* Validate and sanitize user input.

## Purpose of the Project

The main purpose of this system is to provide an organized digital platform for **institutional task governance**.

Instead of managing tasks through informal communication or separate records, the system provides a centralized platform where institutional tasks can be:

* Created
* Assigned
* Tracked
* Updated
* Communicated
* Monitored
* Maintained historically

This helps provide better visibility and accountability for institutional work.

## Future Enhancements

Possible future improvements include:

* Advanced task analytics and dashboards
* Real-time notifications
* Department-wise performance reports
* Calendar-based task management
* Committee creation and management

## Project Status

**Status:** Active Development

The system is being developed as an institutional task management and governance platform for educational institutions.

## Author

**Karthik Sharma**

B.Tech – Computer Science and Engineering
G. Pulla Reddy Engineering College, Kurnool

GitHub: [Nkarthiksharma](https://github.com/Nkarthiksharma)
