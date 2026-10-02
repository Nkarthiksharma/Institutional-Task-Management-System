import pymysql
from flask import Flask, render_template, redirect,url_for,g
from flask_wtf import FlaskForm
from datetime import timedelta
from flask import send_from_directory
from wtforms.validators import DataRequired, Email, Length
from flask import session, request, jsonify
from flask_ckeditor import CKEditor, CKEditorField
from wtforms import StringField, SubmitField, EmailField, PasswordField, DateField, SelectMultipleField
from flask_wtf.file import MultipleFileField, FileAllowed
from datetime import date
import os
from dotenv import load_dotenv
load_dotenv()
from werkzeug.utils import secure_filename
import time
from flask_mail import Mail, Message
from werkzeug.local import LocalProxy

app = Flask(__name__)
app.permanent_session_lifetime = timedelta(days=7)
app.config['SECRET_KEY'] = "My secret key"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = "karthikkvk292@gmail.com"
mail = Mail(app)

ckeditor = CKEditor(app)
# ============================================================
# MULTI-USER DATABASE CONNECTION
# Each request gets its own MySQL connection and cursor.
# ============================================================

def get_db():
    if "db" not in g:
        g.db = pymysql.connect(
            host="localhost",
            user="root",
            password="12345678",
            database="collegeproject",
            charset="utf8mb4",
            autocommit=False
        )
    return g.db


def get_cursor():
    if "cursor" not in g:
        g.cursor = get_db().cursor()
    return g.cursor


# These two lines allow your existing code to continue using:
# cursor.execute(...)
# cursor.fetchone()
# cursor.fetchall()
# conn.commit()
# conn.rollback()
#
# WITHOUT changing your routes.

conn = LocalProxy(get_db)
cursor = LocalProxy(get_cursor)


@app.teardown_appcontext
def close_db(exception=None):

    cursor_obj = g.pop("cursor", None)
    db = g.pop("db", None)

    if cursor_obj is not None:
        cursor_obj.close()

    if db is not None:
        if exception is not None:
            try:
                db.rollback()
            except Exception:
                pass

        db.close()


class login(FlaskForm):
    email = EmailField('Email Address', validators=[DataRequired(message="Enter Email"), Email("Enter valid Email")])
    password = PasswordField('Enter Password', validators=[DataRequired(message="Enter valid Password ")])
    submit = SubmitField('Sign Up')


class createTaskForm(FlaskForm):
    taskName = StringField('Task Name', validators=[DataRequired(message="Enter Task Name")])
    details = CKEditorField('Description', validators=[DataRequired(message="Enter Description")])
    attachment = MultipleFileField(
        "Attachment",
        validators=[
            FileAllowed(
                ["pdf", "doc", "docx", "xls", "xlsx", "txt"],
                "Only Text,PDF, Word, and Excel files are allowed."
            )
        ]
    )
    updateOn = DateField('Report On', validators=[DataRequired()])
    dueDate = DateField('Due Date', validators=[DataRequired()])
    faculty = SelectMultipleField("Faculty", coerce=int)

    submit = SubmitField('Add')


@app.route('/', methods=['GET', 'POST'])
def helloworld():
    loginform = login()
    if loginform.validate_on_submit():
        email = loginform.email.data
        password = loginform.password.data
        cursor.execute("select * from faculty where mail=%s", (email,))
        details = cursor.fetchone()
        if details == None:
            return render_template("login.html", form=loginform, password="false")
        if details:
            orginalpassword = details[5]
            if orginalpassword != password:
                form = None
                print("orginalpassword", orginalpassword)
                print("password", password)
                return render_template("login.html", form=loginform, password="false")
            else:
                id = details[0]
                name = details[1]
                dept = details[2]
                desig = details[3]
                power = details[6]
                session["desig"]=desig
                session["power"] = power
                session["loggedin"] = 0
                if power == 2:
                    session["loggedin"] = 1
                    return redirect("/principal-control")
                elif power == 1:
                    session["dept"] = dept
                    session["id"] = id
                    session["loggedin"] = 1
                    return redirect("/hod-control")
                elif power == 0:
                    session["id"] = id
                    session["loggedin"] = 1
                    return redirect("/myTasks")

    return render_template("login.html", form=loginform, password="notyet")

# ============================================================================
# PIE DIAGRAM CALCULATION ENGINE: UNIQUE TASKS (LEVEL 1) & ASSIGNMENTS (LEVEL 2)
# ============================================================================

# ============================================================================
# PIE DIAGRAM DATA CALCULATION: ONGOING, COMPLETED, TOTAL
# ============================================================================

# ============================================================================
# PIE DIAGRAM DATA CALCULATION: ONGOING, COMPLETED, TOTAL
# ============================================================================

def get_pie_diagram_stats(dept_filter=None):
    """
    Computes exact counts for:
    - Level 1 Unique Tasks:
        * Completed: ALL assigned faculty have completed (status=1)
        * Ongoing:   In-progress, partial, or pending
        * Total:     Unique tasks count
    - Level 2 Faculty Assignments:
        * Completed: status = 1
        * Ongoing:   status != 1
        * Total:     Total faculty assignments count
    """
    db_cursor = get_cursor()

    if dept_filter and dept_filter.lower() != "all":
        db_cursor.execute("""
            SELECT 
                t.id AS task_id,
                tm.facultyid,
                tm.status
            FROM tasks t
            JOIN taskmanagements tm ON t.id = tm.taskid
            JOIN faculty f ON tm.facultyid = f.id
            WHERE LOWER(f.dept) = %s
        """, (dept_filter.lower(),))
    else:
        db_cursor.execute("""
            SELECT 
                t.id AS task_id,
                tm.facultyid,
                tm.status
            FROM tasks t
            JOIN taskmanagements tm ON t.id = tm.taskid
            JOIN faculty f ON tm.facultyid = f.id
        """)

    rows = db_cursor.fetchall()

    grouped_tasks = {}
    total_assignments = 0
    assign_completed = 0
    assign_ongoing = 0

    for row in rows:
        task_id = row[0]
        status = int(row[2])

        total_assignments += 1

        if status == 1:
            assign_completed += 1
            assign_state = "Completed"
        else:
            assign_ongoing += 1
            assign_state = "Ongoing"

        if task_id not in grouped_tasks:
            grouped_tasks[task_id] = []
        grouped_tasks[task_id].append(assign_state)

    # Unique tasks: Completed iff every assigned faculty finished
    task_total = len(grouped_tasks)
    task_completed = 0
    task_ongoing = 0

    for task_id, assignments in grouped_tasks.items():
        k = len(assignments)
        comp_count = assignments.count("Completed")

        if k > 0 and comp_count == k:
            task_completed += 1
        else:
            task_ongoing += 1

    return {
        "task_ongoing": task_ongoing,
        "task_completed": task_completed,
        "task_total": task_total,
        "assign_ongoing": assign_ongoing,
        "assign_completed": assign_completed,
        "assign_total": total_assignments
    }


# ============================================================================
# PRINCIPAL CONTROL CENTER ROUTE
# ============================================================================

@app.route("/principal-control")
@app.route("/principal-report")
def principal_control():
    if not session.get("loggedin") or session.get("power") != 2:
        return redirect("/")

    selected_dept = request.args.get("department", "all").strip()
    stats = get_pie_diagram_stats(selected_dept)

    principal_name = session.get("name")
    if not principal_name:
        cursor.execute("SELECT name FROM faculty WHERE power = 2 and desig=%s LIMIT 1",(session["desig"]))
        row = cursor.fetchone()
        principal_name = row[0] if row else "Principal"

    cursor.execute("SELECT DISTINCT dept FROM faculty WHERE dept IS NOT NULL AND dept != '' ORDER BY dept")
    departments = [r[0].upper() for r in cursor.fetchall()]

    return render_template(
        "principal_control.html",
        principal_name=principal_name,
        selected_dept=selected_dept,
        departments=departments,
        stats=stats
    )


# ============================================================================
# HOD CONTROL CENTER ROUTE
# ============================================================================

@app.route("/hod-control")
@app.route("/hod-report")
def hod_control():
    if not session.get("loggedin") or session.get("power") != 1:
        return redirect("/")

    hod_dept = session.get("dept", "").upper()
    stats = get_pie_diagram_stats(hod_dept)

    hod_name = session.get("name")
    if not hod_name and session.get("id"):
        cursor.execute("SELECT name FROM faculty WHERE id = %s", (session.get("id"),))
        row = cursor.fetchone()
        hod_name = row[0] if row else "Head of Department"

    return render_template(
        "hod_control.html",
        hod_name=hod_name,
        dept=hod_dept,
        stats=stats
    )
@app.route('/seggregate', methods=['GET', 'POST'])
def seggregate():
    if session.get("loggedin") == 0 or session.get("power") == 0 or session.get("loggedin") == None or session.get(
            "power") == None:
        return redirect("/")
    data = request.get_json()
    dept = data["dept"].lower()
    status = int(data["status"])
    tasks = []
    nooftasks = ()
    if dept != "all":
        cursor.execute("select * from taskmanagements tm join faculty f on f.id=tm.facultyid  where f.dept=%s", (dept,))
        total_no_of_tasks = cursor.fetchall()
        number_of_tasks_assigned = len(total_no_of_tasks)
        cursor.execute(
            "select * from taskmanagements tm join faculty f on f.id=tm.facultyid   where tm.status=%s and f.dept=%s",
            (0, dept))
        ongoing_tasks = cursor.fetchall()
        no_of_assigned_ongoing_tasks = len(ongoing_tasks)
        no_of_assigned_completed_tasks = number_of_tasks_assigned - no_of_assigned_ongoing_tasks
        nooftasks = (number_of_tasks_assigned, no_of_assigned_ongoing_tasks, no_of_assigned_completed_tasks)
    if dept == "all":
        cursor.execute("select * from taskmanagements ")
        total_no_of_tasks = cursor.fetchall()
        number_of_tasks_assigned = len(total_no_of_tasks)
        cursor.execute("select * from taskmanagements where status=%s ", (0,))
        ongoing_tasks = cursor.fetchall()
        no_of_assigned_ongoing_tasks = len(ongoing_tasks)
        no_of_assigned_completed_tasks = number_of_tasks_assigned - no_of_assigned_ongoing_tasks
        nooftasks = (number_of_tasks_assigned, no_of_assigned_ongoing_tasks, no_of_assigned_completed_tasks)
        if status == 2:
            cursor.execute("""SELECT t.id,
                                     t.name,
                                     f.id
                                         AS
                                         faculty_id,
                                     f.name
                                         AS
                                         faculty_name,
                                     f.dept,
                                     t.createdon,
                                     t.updateon,
                                     tm.status,
                                     t.duedate,
                                     t.createdby,
                                     tm.textinfo


                              FROM tasks t
                                       JOIN
                                   taskmanagements tm
                                   ON
                                       t.id = tm.taskid
                                       JOIN
                                   faculty f
                                   ON
                                       tm.facultyid = f.id

                           """)
            tasks = cursor.fetchall()
        else:
            cursor.execute("""SELECT t.id,
                                     t.name,
                                     f.id
                                         AS
                                         faculty_id,
                                     f.name
                                         AS
                                         faculty_name,
                                     f.dept,
                                     t.createdon,
                                     t.updateon,
                                     tm.status,
                                     t.duedate,
                                     t.createdby,
                                     tm.textinfo


                              FROM tasks t
                                       JOIN
                                   taskmanagements tm
                                   ON
                                       t.id = tm.taskid
                                       JOIN
                                   faculty f
                                   ON
                                       tm.facultyid = f.id
                              where tm.status = %s
                           """, (status,))
            tasks = cursor.fetchall()

    elif (status == 1 or status == 0):

        cursor.execute("""SELECT t.id,
                                 t.name,
                                 f.id
                                     AS
                                     faculty_id,
                                 f.name
                                     AS
                                     faculty_name,
                                 f.dept,
                                 t.createdon,
                                 t.updateon,
                                 tm.status,
                                 t.duedate,
                                 t.createdby,
                                 tm.textinfo


                          FROM tasks t
                                   JOIN
                               taskmanagements tm
                               ON
                                   t.id = tm.taskid
                                   JOIN
                               faculty f
                               ON
                                   tm.facultyid = f.id
                          where tm.status = %s
                            and f.dept = %s
                       """, (status, dept))
        tasks = cursor.fetchall()
    elif status == 2:
        cursor.execute("""SELECT t.id,
                                 t.name,
                                 f.id
                                     AS
                                     faculty_id,
                                 f.name
                                     AS
                                     faculty_name,
                                 f.dept,
                                 t.createdon,
                                 t.updateon,
                                 tm.status,
                                 t.duedate,
                                 t.createdby,
                                 tm.textinfo


                          FROM tasks t
                                   JOIN
                               taskmanagements tm
                               ON
                                   t.id = tm.taskid
                                   JOIN
                               faculty f
                               ON
                                   tm.facultyid = f.id
                          where f.dept = %s
                       """, (dept,))
        tasks = cursor.fetchall()

    for task in tasks:
        print(task[0], task[1], task[2], task[3], task[4], task[5], task[6], task[7], task[8], task[9], task[10])
    return jsonify({"tasks": tasks, "count": nooftasks})


@app.route('/Principal')
def Principal():
    if session.get("loggedin") == 0 or session.get("power") != 2 or session.get("loggedin") == None or session.get(
            "power") == 0:
        return redirect("/")
    session["created"] = "False"
    print(session.get("created"))
    cursor.execute("select * from taskmanagements")
    total_no_of_tasks = cursor.fetchall()
    number_of_tasks_assigned = len(total_no_of_tasks)
    cursor.execute("select * from taskmanagements where status=%s", (0,))
    ongoing_tasks = cursor.fetchall()
    no_of_assigned_ongoing_tasks = len(ongoing_tasks)
    no_of_assigned_completed_tasks = number_of_tasks_assigned - no_of_assigned_ongoing_tasks
    cursor.execute("""SELECT t.id,
                             t.name,
                             f.id
                                 AS
                                 faculty_id,
                             f.name
                                 AS
                                 faculty_name,
                             f.dept,
                             t.createdon,
                             t.updateon,
                             tm.status,
                             t.duedate,
                             t.createdby,
                             tm.textinfo

                      FROM tasks t
                               JOIN
                           taskmanagements tm
                           ON
                               t.id = tm.taskid
                               JOIN
                           faculty f
                           ON
                               tm.facultyid = f.id
                   """)
    tasks = cursor.fetchall()
    return render_template("Principal.html", power=2, total_tasks=tasks, assigned=number_of_tasks_assigned,
                           ongoing=no_of_assigned_ongoing_tasks, completed=no_of_assigned_completed_tasks)


@app.route('/backbutton',methods=['GET'])
def backbutton():
    if session.get("power")==2:
      return redirect("/Principal")
    elif session.get("power")==1:
      return redirect("/HOD")
    elif session.get("power")==0:
        return redirect("/logout")
@app.route('/HOD', methods=['GET', 'POST'])
def hod():
    if session.get("loggedin") == 0 or session.get("power") != 1 or session.get("loggedin") == None or session.get(
            "power") == 0:
        return redirect("/")
    session["created"] = "False"
    dept = session.get("dept").upper()
    cursor.execute("select * from taskmanagements t join faculty f on t.facultyid=f.id where f.dept= %s", (dept,))
    total_no_of_tasks = cursor.fetchall()
    number_of_tasks_assigned = len(total_no_of_tasks)
    cursor.execute("select * from taskmanagements t join faculty f on t.facultyid=f.id where f.dept=%s and status=%s",
                   (dept, 0,))
    ongoing_tasks = cursor.fetchall()
    no_of_assigned_ongoing_tasks = len(ongoing_tasks)
    no_of_assigned_completed_tasks = number_of_tasks_assigned - no_of_assigned_ongoing_tasks
    cursor.execute("""SELECT t.id,
                             t.name,
                             f.id
                                 AS
                                 faculty_id,
                             f.name
                                 AS
                                 faculty_name,
                             f.dept,
                             t.createdon,
                             t.updateon,
                             tm.status,
                             t.duedate,
                             t.createdby,


                             tm.textinfo


                      FROM tasks t
                               JOIN
                           taskmanagements tm
                           ON
                               t.id = tm.taskid
                               JOIN
                           faculty f
                           ON
                               tm.facultyid = f.id
                      where f.dept = %s
                   """, (dept,))
    tasks = cursor.fetchall()
    for task in tasks:
        print(task[0], task[1], task[2], task[3], task[4], task[5], task[6], task[7], task[8], task[9], )
    return render_template("Principal.html", power=1, dept=dept.lower(), total_tasks=tasks,
                           assigned=number_of_tasks_assigned,
                           ongoing=no_of_assigned_ongoing_tasks, completed=no_of_assigned_completed_tasks)


@app.route("/createtask", methods=['GET', 'POST'])
def createTask():
    if session.get("loggedin") == 0 or session.get("power") == 0 or session.get("loggedin") == None or session.get(
            "power") == 0:
        return redirect("/")
    if session.get("created") == "True":
        taskForm = createTaskForm()

        return render_template("Create.html", form=taskForm, created=True, name=session.get("taskName"))
    taskForm = createTaskForm()
    if session.get("power") == 2:
        cursor.execute("select id,name,desig,dept,mail from faculty where power!=%s", (2,))
    elif session.get("power") == 1:
        cursor.execute("select id,name,desig,dept,mail from faculty where dept=%s and power=%s",
                       (session.get("dept"), 0))
    rows = cursor.fetchall()
    taskForm.faculty.choices = [
        (row[0], f"ID: {row[0]} {row[1]}  {row[2]}  {row[3]}") for row in rows
    ]

    if taskForm.validate_on_submit():

        taskName = taskForm.taskName.data
        attachments = taskForm.attachment.data

        details = taskForm.details.data
        updateOn = taskForm.updateOn.data
        dueDate = taskForm.dueDate.data
        facultyIdList = taskForm.faculty.data
        createdBy = None
        if (session.get("power") == 1):
            if session.get("dept") == "CSE":
                createdBy = "CSEHOD"
            elif session.get("dept") == "CSM":
                createdBy = "CSMHOD"
            elif session.get("dept") == "ECE":
                createdBy = "ECEHOD"
            elif session.get("dept") == "EEE":
                createdBy = "EEEHOD"
        elif (session.get("power") == 2):

            createdBy = session.get("desig")
        print(taskName, details, updateOn, dueDate, facultyIdList[0], createdBy)

        today = date.today()
        cursor.execute(
            "insert into tasks( name, details ,updateon,duedate, createdby,createdon) values(%s,%s,%s,%s,%s,%s)",
            (taskName, details, updateOn, dueDate, createdBy, today))
        taskId = cursor.lastrowid
        if attachments:
            for file in attachments:
                if file.filename != None:
                    original_name = secure_filename(file.filename)
                    stored_name = str(int(time.time() * 1000)) + "_" + original_name
                    file.save(
                        os.path.join(
                            app.config["UPLOAD_FOLDER"],
                            stored_name
                        )
                    )
                    cursor.execute(
                        """
                        INSERT INTO attachments(taskid, orginalname, storedname)
                        VALUES (%s, %s, %s)
                        """,
                        (
                            taskId,
                            original_name,
                            stored_name
                        )
                    )
        mailrows = []
        for id in facultyIdList:
            cursor.execute("insert into taskmanagements(taskid,facultyid,status,textinfo) values (%s,%s,%s,%s)",
                           (taskId, id, 0, ""))
            cursor.execute("select mail from faculty where id=%s", (id,))
            rows = cursor.fetchone()
            mailrows.append(rows[0])

        session["created"] = "True"
        session["taskName"] = taskName
        for mails in mailrows:
            msg = Message(
                subject="A New Task Created",
                recipients=[mails]
            )
            if session.get("power") == 2:
                desig=session.get("desig")
                msg.body = f"Complete the Task {taskName} ASAP\nRegards {desig}"
            elif session.get("power") == 1:
                msg.body = f"Complete the Task {taskName} ASAP\nRegards Head Of the Department"
            try:
                mail.send(msg)
                print("Email sent")
            except Exception as e:
                print("Error")
        conn.commit()
        return render_template("Create.html", form=taskForm, created=True, name=taskName)

    return render_template("Create.html", form=taskForm, created=False, name="")


@app.route("/myTasks", methods=["GET", "POST"])
def myTasks():
    if session.get("loggedin") == 0 or session.get("loggedin") == None:
        return redirect("/")
    name = None
    dept = None
    id = None
    cursor.execute("select id,name,dept from faculty where id =%s", (session.get("id"),))
    facultyrow = cursor.fetchone()

    name = facultyrow[1]
    dept = facultyrow[2]
    id = facultyrow[0]
    cursor.execute("select taskid from taskmanagements where facultyid=%s", (session.get("id"),))
    taskidlist = cursor.fetchall()
    taskList = []
    for row in taskidlist:
        taskid = row[0]
        t = []
        cursor.execute("select id,name,duedate,createdby from tasks where id=%s", (taskid,))
        onetask = cursor.fetchone()
        if not onetask:
            continue
        t.append(onetask[0])
        t.append(onetask[1])
        t.append(onetask[2])
        t.append(onetask[3])

        cursor.execute("select status from taskmanagements where taskid=%s and facultyid=%s", (taskid, id))
        status_textinfo = cursor.fetchone()
        status = status_textinfo[0]

        t.append(status)

        taskList.append(t)
    return render_template("myTasks.html", taskList=taskList, myid=id, myname=name, mydept=dept)

@app.route("/myTasksDetailly", methods=["GET", "POST"])
def myTasksDetailly():
    if session.get("loggedin") == 0 or session.get("loggedin") == None:
        return redirect("/")
    name = None
    dept = None
    id = None
    cursor.execute("select id,name,dept from faculty where id =%s", (session.get("id"),))
    facultyrow = cursor.fetchone()

    name = facultyrow[1]
    dept = facultyrow[2]
    id = facultyrow[0]
    taskid = request.args.get('taskid')

    taskid = request.args.get("taskid")

    if taskid:
        try:
            taskid = int(taskid)
            session["taskid"] = taskid
        except ValueError:
            return "Invalid Task ID", 400

    else:
        taskid = session.get("taskid")

        if not taskid:
            return "Invalid Task ID", 400
    cursor.execute("select taskid from taskmanagements where facultyid=%s and taskid=%s ", (session.get("id"),taskid))
    task = cursor.fetchone()

    if not task:
        return "Task not found or unauthorized", 404



    cursor.execute("select * from tasks where id=%s", (taskid,))

    onetask = cursor.fetchone()
    t = []
    if not onetask:
        return "Task not found or unauthorized", 404
    t.append(onetask[0])
    t.append(onetask[1])
    t.append(onetask[2])
    t.append(onetask[6])
    t.append(onetask[3])
    t.append(onetask[4])
    t.append(onetask[5])
    cursor.execute("select status,textinfo from taskmanagements where taskid=%s and facultyid=%s", (taskid, id))
    status_textinfo = cursor.fetchone()
    status = status_textinfo[0]
    textinfo = status_textinfo[1]
    t.append(status)
    t.append(textinfo)
    cursor.execute(
            "SELECT orginalname, storedname FROM attachments WHERE taskid=%s",
            (taskid,)
        )
    attachments = cursor.fetchall()

    t.append(attachments)
    cursor.execute(
        """
        SELECT remarks
        FROM taskmanagement_history
        WHERE taskid=%s AND facultyid=%s
        ORDER BY version ASC
        """,
        (taskid, id)
    )

    message_history = cursor.fetchall()
    t.append(message_history)
    return render_template("myTasksDetailly.html", taskList=t, myid=id, myname=name, mydept=dept)
@app.route("/updateTask", methods=["POST"])
def updateTask():

    if session.get("loggedin") == 0:
        return redirect("/")

    facultyId = int(session.get("id"))
    taskid = int(request.form.get("taskid"))
    status = int(request.form.get("status"))
    remarks = request.form.get("textinfo").strip()
    if not remarks:
        return redirect("/myTasksDetailly")

    # Current version
    cursor.execute("""
        SELECT version
        FROM taskmanagement_history
        WHERE taskid=%s
        AND facultyid=%s
        AND current_record=1
    """,(taskid,facultyId))

    row=cursor.fetchone()

    if row is None:
        version=1
    else:
        version=row[0]+1

        cursor.execute("""
            UPDATE taskmanagement_history
            SET
                current_record=0,
                valid_to=NOW()
            WHERE
                taskid=%s
                AND facultyid=%s
                AND current_record=1
        """,(taskid,facultyId))

    cursor.execute("""
        INSERT INTO taskmanagement_history
        (
            taskid,
            facultyid,
            status,
            remarks,
            version,
            valid_from,
            valid_to,
            current_record,
            updated_by
        )
        VALUES
        (
            %s,%s,%s,%s,
            %s,
            NOW(),
            NULL,
            1,
            %s
        )
    """,
    (
        taskid,
        facultyId,
        status,
        remarks,
        version,
        facultyId
    ))

    cursor.execute("""
        UPDATE taskmanagements
        SET
            status=%s,
            textinfo=%s
        WHERE
            taskid=%s
            AND facultyid=%s
    """,
    (
        status,
        remarks,
        taskid,
        facultyId
    ))

    conn.commit()

    return redirect("/myTasksDetailly")

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/createdTasks", methods=["GET", "POST"])
def createdTasks():
    if session.get("loggedin") == 0 or session.get("power") == 0 or session.get("loggedin") == None or session.get(
            "power") == 0:
        return redirect("/")
    if session.get("power") == 2:
        session["taskId"] = None
        desig=session.get("desig")
        cursor.execute("select * from tasks where createdby=%s", (desig,))
        rows = cursor.fetchall()
        return render_template("createdTasks.html", rows=rows)
    elif session.get("power") == 1:
        session["taskId"] = None
        if session.get("dept") == "CSE":
            cursor.execute("select * from tasks where createdby=%s  ", ("CSEHOD",))
        elif session.get("dept") == "CSM":
            cursor.execute("select * from tasks where createdby=%s  ", ("CSMHOD",))
        elif session.get("dept") == "ECE":
            cursor.execute("select * from tasks where createdby=%s  ", ("ECEHOD",))
        elif session.get("dept") == "EEE":
            cursor.execute("select * from tasks where createdby=%s  ", ("EEEHOD",))
        rows = cursor.fetchall()
        return render_template("createdTasks.html", rows=rows)



@app.route("/updateTaskByAuthor", methods=["GET", "POST"])
def updateTaskByAuthor():

    if session.get("loggedin") != 1 or session.get("power") == 0:
        return redirect("/")

    # GET from hyperlink
    if request.method == "GET":
        id = request.args.get("id")

        if not id:
            return "Invalid Task ID", 400

        try:
            id = int(id)
        except ValueError:
            return "Invalid Task ID", 400

        session["taskId"] = id

    # POST from your existing forms
    else:
        id = request.form.get("id")

        if not id:
            print(id)
            return "Invalid Task ID", 400

        try:
            id = int(id)
            print(id)
        except ValueError:
            return "Invalid Task ID", 400

        session["taskId"] = id

    # ============================================================
    # CHECK WHETHER THIS TASK CAN BE ACCESSED
    # ============================================================

    # ============================================================
    # TASK ACCESS CHECK
    # ============================================================

    cursor.execute("""
        SELECT id, createdby
        FROM tasks
        WHERE id = %s
    """, (id,))

    task_access = cursor.fetchone()

    if not task_access:
        return "Task Not Found", 404

    createdby = task_access[1]

    # Principal can access all tasks
    if session.get("power") == 2:

        expected_creator = desig=session.get("desig")

    # HOD access check
    elif session.get("power") == 1:

        # Get logged-in HOD department
        cursor.execute(
            "SELECT dept FROM faculty WHERE id = %s",
            (session.get("id"),)
        )

        hod = cursor.fetchone()

        if not hod:
            return "You cannot have access to modify the task", 403

        hod_dept = hod[0]

        # Your database stores creators as:
        # CSEHOD, CSMHOD, ECEHOD, EEEHOD
        expected_creator = hod_dept + "HOD"

        # HOD can only access tasks created by their own HOD
        if createdby != expected_creator:
            return "Unauthorized", 403
    else:

        return "You cannot have access to modify the task  created by principal or other department HOD", 403
    if createdby != expected_creator:
        return "You cannot have access to modify this task,because the task is not created by you ", 403
    cursor.execute("select id,name,details,createdon,updateon,duedate from tasks where id=%s", (id,))
    taskDetails = cursor.fetchall()

    cursor.execute(
        "select f.id,f.name,f.dept,t.status,t.textinfo,t.id from taskmanagements t join faculty f on f.id=t.facultyid where t.taskid=%s",
        (id,))
    facultyDetails = cursor.fetchall()
    for faculty in facultyDetails:
        print(faculty[0], faculty[1], faculty[2], faculty[3], faculty[4])
    cursor.execute(
        "SELECT orginalname,storedname,id FROM attachments WHERE taskid=%s",
        (id,)
    )
    attachments = cursor.fetchall()
    if session.get("power") == 2:
        cursor.execute("select id,name,desig,dept,mail from faculty where power!=%s", (2,))
    elif session.get("power") == 1:
        cursor.execute("select id,name,desig,dept,mail from faculty where dept=%s and power=%s",
                       (session.get("dept"), 0))
    rows = cursor.fetchall()
    faculty_choices = [
        (row[0], f"ID: {row[0]} {row[1]}  {row[2]}  {row[3]}") for row in rows
    ]
    cursor.execute("""
    SELECT
        h.taskid,
        h.facultyid,
        f.name,
        h.version,
        h.status,
        h.remarks,
        h.valid_from,
        h.valid_to,
        h.current_record
    FROM taskmanagement_history h
    JOIN faculty f
        ON h.facultyid = f.id
    WHERE h.taskid = %s
    ORDER BY h.facultyid, h.version DESC
    """, (id,))

    historyDetails = cursor.fetchall()
    return render_template("updateTaskByAuthor.html", taskDetails=taskDetails, facultyDetails=facultyDetails,
                           attachments=attachments, faculty_choices=faculty_choices,historyDetails=historyDetails)

@app.route("/saveTaskChanges", methods=["POST"])
def saveTaskChanges():

    if session.get("loggedin") == 0 or session.get("power") == 0:
        return redirect("/")

    taskId = int(request.form.get("taskid"))

    description = request.form.get("description")
    reportDate = request.form.get("reportDate")
    dueDate = request.form.get("dueDate")

    try:

        # -----------------------------
        # Update Task Details
        # -----------------------------

        cursor.execute("""
            UPDATE tasks
            SET
                details=%s,
                updateon=%s,
                duedate=%s
            WHERE id=%s
        """,(description,reportDate,dueDate,taskId))

        # -----------------------------
        # Delete Selected Attachments
        # -----------------------------

        deleteFiles=request.form.getlist("delete_files")

        for fileId in deleteFiles:

            cursor.execute(
                "SELECT storedname FROM attachments WHERE id=%s",
                (fileId,)
            )

            row=cursor.fetchone()

            if row:

                filepath=os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    row[0]
                )

                if os.path.exists(filepath):
                    os.remove(filepath)

                cursor.execute(
                    "DELETE FROM attachments WHERE id=%s",
                    (fileId,)
                )

        # -----------------------------
        # Upload New Files
        # -----------------------------

        files=request.files.getlist("files")

        for file in files:

            if file and file.filename:

                original_name=secure_filename(file.filename)

                stored_name=str(int(time.time()*1000))+"_"+original_name

                file.save(
                    os.path.join(
                        app.config["UPLOAD_FOLDER"],
                        stored_name
                    )
                )

                cursor.execute("""
                    INSERT INTO attachments
                    (taskid,orginalname,storedname)
                    VALUES(%s,%s,%s)
                """,(
                    taskId,
                    original_name,
                    stored_name
                ))
        # -----------------------------
        # Remove Faculty
        # -----------------------------

        removeFaculty = request.form.getlist("removeFaculty")

        for tmid in removeFaculty:

            cursor.execute(
                "DELETE FROM taskmanagements WHERE id=%s",
                (tmid,)
            )

        # -----------------------------
        # Add New Faculty
        # -----------------------------

        facultyList = request.form.getlist("faculty")

        cursor.execute(
            "SELECT name FROM tasks WHERE id=%s",
            (taskId,)
        )

        taskRow = cursor.fetchone()

        taskName = taskRow[0]

        mailrows = []

        for facultyId in facultyList:

            # Prevent duplicate assignment
            cursor.execute(
                """
                SELECT id
                FROM taskmanagements
                WHERE taskid=%s
                AND facultyid=%s
                """,
                (taskId, facultyId)
            )

            alreadyAssigned = cursor.fetchone()

            if alreadyAssigned:
                continue

            cursor.execute(
                """
                INSERT INTO taskmanagements
                (taskid,facultyid,status,textinfo)
                VALUES(%s,%s,%s,%s)
                """,
                (taskId, facultyId, 0, "")
            )

            cursor.execute(
                "SELECT mail FROM faculty WHERE id=%s",
                (facultyId,)
            )

            row = cursor.fetchone()

            if row:
                mailrows.append(row[0])

        # -----------------------------
        # Send Mail
        # -----------------------------

        for mails in mailrows:

            msg = Message(
                subject="A New Task Created",
                recipients=[mails]
            )

            if session.get("power") == 2:
                msg.body = f"Complete the Task '{taskName}' ASAP.\n\nRegards,\nPrincipal"
            else:
                msg.body = f"Complete the Task '{taskName}' ASAP.\n\nRegards,\nHead of Department"

            try:
                mail.send(msg)
            except Exception as e:
                print("Mail Error:", e)

        # -----------------------------
        # Save Everything
        # -----------------------------

        conn.commit()

    except Exception as e:

        conn.rollback()

        print(e)

    return redirect(url_for("updateTaskByAuthor", id=taskId))
@app.route('/logout')
def logout():


    session.clear()  # Clears user session data
    return redirect('/')  # Redirects user back to login page
if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True,port=5004)
