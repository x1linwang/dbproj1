
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of:
#
#     postgresql://USER:PASSWORD@34.75.150.200/proj1part2
#
# For example, if you had username gravano and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://gravano:foobar@34.75.150.200/proj1part2"
#
DATABASEURI = "postgresql://xw2767:7210@34.75.150.200/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
#
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#

@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print(request.args)


  #
  # example of a database query
  #
  cursor = g.conn.execute("""
                            SELECT R.name, AVG(UR.rating)
                            FROM Restaurant R, u_writes_for UW, User_Reviews UR
                            WHERE R.rid = UW.rid
                            AND UW.urid = UR.urid
                            GROUP BY R.name
                            ORDER BY AVG(UR.rating) DESC
                            LIMIT 10;
                            """)
  names = []
  for result in cursor:
      response = "Name: " + str(result[0]) + ", " + "Average rating: " + str(round(result[1],2)) + "."
      names.append(response)
  cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #
  #     # creates a <div> tag for each element in data
  #     # will print:
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data = names)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)




# general query returns everything we have about the restaurant
# including the contact info, category, location, user rating,
# order type and special dietary needs it satisfies

@app.route('/generalquery', methods=['POST'])
def generalquery():
    name = str(request.form['name'])
    info = []

    # this is to check if the restaurant queried is in our database
    query = text("""SELECT name, website, phone, category
                FROM Restaurant
                Where name = '{}'
                """.format(name))

    cursor = g.conn.execute(query)
    row = cursor.fetchone()
    if row == None: # retaurant is not in the database, app will show an error page
        message = "The restaurant you searched for is not in our database. Please check if you typed the name wrong or try searching for another restaurant."
        info.append(message)
        context = dict(data = info)
        return render_template("error.html", **context)
    else: # otherwise, add the restaurant info to the list
        info.append(row['name'])
        info.append(row['website'])
        info.append(row['phone'])
        info.append("Categoty: "+str(row['category']))
    cursor.close

    query = text("""SELECT I.number, I.street, I.city, I.zip
                    FROM Restaurant R, Is_at_Locations I
                    WHERE R.name = '{}' AND R.rid = I.rid;
                    """.format(name))
    cursor = g.conn.execute(query)

    row = cursor.fetchone()
    address = "Address: "+str(row['number'])+" "+row['street']+" "+row['city']+" "+str(row['zip'])
    info.append(address)
    cursor.close()

    query = text("""SELECT AVG(UR.rating)
                FROM Restaurant R, u_writes_for UW, User_Reviews UR
                WHERE R.name = '{}' AND R.rid = UW.rid AND UW.urid = UR.urid
                """.format(name))

    cursor = g.conn.execute(query)

    for result in cursor:
        for thing in result:
            info.append("Average Rating: "+str(round(thing,2)))
    cursor.close()

    query = text("""SELECT O.type
        FROM Restaurant R, offers O
        Where R.name = '{}' AND R.rid = O.rid;
        """.format(name))

    cursor = g.conn.execute(query)

    orderoption = "Order options: "

    for row in cursor:
        orderoption += (row['type']+" ")
    cursor.close()

    info.append(orderoption)

    query = text("""SELECT S.name
                FROM Restaurant R, Satisfies S
                Where R.name = '{}' AND R.rid = S.rid;
                """.format(name))

    cursor = g.conn.execute(query)

    dietaryneed = "Dietary need: "

    for row in cursor:
        dietaryneed += (row['name']+" ")
    cursor.close()

    info.append(dietaryneed)

    context = dict(data = info)
    return render_template("query.html", **context)

@app.route('/catquery', methods=['POST'])
def catquery():
    cat = str(request.form['cat'])

    query = text("""SELECT R.name
                FROM Restaurant R
                WHERE R.category = '{}';
                """.format(cat))
    cursor = g.conn.execute(query)
    row = cursor.fetchone()
    info = []

    if row == None:
        cursor.close()
        message1 = "The restaurant categoty '"+cat+"' is not found in our database."
        message2 = "The only allowed categories for now are: Chinese, Indian, American, Italian, Mexican, Japanese."
        info.append(message1)
        info.append(message2)
        context = dict(data = info)
        return render_template("error.html", **context)

    info.append("Top 20 restaurants in category: "+cat)

    query = text("""SELECT R.name
                FROM Restaurant R, u_writes_for UW, User_Reviews UR
                WHERE R.category = '{}'
                AND R.rid = UW.rid
                AND UW.urid = UR.urid
                GROUP BY R.name
                ORDER BY AVG(UR.rating)
                LIMIT 20;
                """.format(cat))

    cursor = g.conn.execute(query)

    for result in cursor:
        info.append(result[0])
    cursor.close()

    context = dict(data = info)

    return render_template("query.html", **context)

@app.route('/dietaryquery', methods=['POST'])
def dietaryquery():
    dietary = str(request.form['dietary'])
    info = []

    query = text("""SELECT R.name
                FROM Restaurant R, Satisfies S
                WHERE S.name = '{}'
                AND R.rid = S.rid;
                """.format(dietary))

    cursor = g.conn.execute(query)
    row = cursor.fetchone()
    info = []

    if row == None:
        cursor.close()
        message1 = "The dietary need '"+dietary+"' is not found in our database."
        message2 = "The only dietary needs available for now are: Vegan, Vegetarian, Halal, Gluten Free."
        info.append(message1)
        info.append(message2)
        context = dict(data = info)
        return render_template("error.html", **context)


    info.append("Top 20 restaurants that offer "+dietary+" dishes:")

    query = text("""SELECT R.name
                FROM Restaurant R, u_writes_for UW, User_Reviews UR, Satisfies S
                WHERE S.name = '{}'
                AND R.rid = S.rid
                AND R.rid = UW.rid
                AND UW.urid = UR.urid
                GROUP BY R.name
                ORDER BY AVG(UR.rating)
                LIMIT 20;
                """.format(dietary))

    cursor = g.conn.execute(query)

    for result in cursor:
        info.append(result[0])
    cursor.close()

    context = dict(data = info)

    return render_template("query.html", **context)

@app.route('/ordertypequery', methods=['POST'])
def ordertypequery():
    ordertype = str(request.form['ordertype'])
    info = []

    query = text("""SELECT R.name
                FROM Restaurant R, offers O
                WHERE O.type = '{}'
                AND R.rid = O.rid;
                """.format(ordertype))

    cursor = g.conn.execute(query)
    row = cursor.fetchone()
    info = []

    if row == None:
        cursor.close()
        message1 = "The order option '"+ordertype+"' is not found in our database."
        message2 = "The only order options available for now are: dine-in, take-out, delivery."
        info.append(message1)
        info.append(message2)
        context = dict(data = info)
        return render_template("error.html", **context)

    info.append("Top 20 restaurants that offer "+ordertype+" service:")

    query = text("""SELECT R.name
                FROM Restaurant R, u_writes_for UW, User_Reviews UR, Offers O
                WHERE O.type = '{}'
                AND R.rid = O.rid
                AND R.rid = UW.rid
                AND UW.urid = UR.urid
                GROUP BY R.name
                ORDER BY AVG(UR.rating)
                LIMIT 20;
                """.format(ordertype))

    cursor = g.conn.execute(query)

    for result in cursor:
        info.append(result[0])
    cursor.close()

    context = dict(data = info)

    return render_template("query.html", **context)

@app.route('/ratingquery', methods=['POST'])
def ratingquery():
    info = []
    try:
        rating = float(request.form['rating'])
    except:
        message1 = "Rating must be a number between 0 and 5. Please check your input."
        info.append(message1)
        context = dict(data = info)
        return render_template("error.html", **context)
    if rating < 0  or rating > 5:
        message1 = "Rating must be a number between 0 and 5. Please check your input."
        info.append(message1)
        context = dict(data = info)
        return render_template("error.html", **context)

    info.append("Restaurants that has rating above "+str(rating)+":")

    query = text("""SELECT R.name
                FROM Restaurant R, u_writes_for UW, User_Reviews UR
                WHERE R.rid = UW.rid
                AND UW.urid = UR.urid
                GROUP BY R.name
                HAVING AVG(UR.rating)>{};
                """.format(rating))

    cursor = g.conn.execute(query)

    for result in cursor:
        info.append(result[0])
    cursor.close()

    context = dict(data = info)

    return render_template("query.html", **context)

@app.route('/resreviewquery', methods=['POST'])
def resreviewquery():
    name = str(request.form['name'])
    info = []
    linebreak = "--------------------"

    query = text("""Select R.name
                    From Restaurant R, User_Reviews UR, u_writes_for UW
                    WHERE R.name = '{}'
                    AND UW.rid = R.rid
                    AND UW.urid = UR.urid;
                """.format(name))

    cursor = g.conn.execute(query)
    row = cursor.fetchone()
    info = []

    if row == None:
        cursor.close()
        message1 = "The restaurant '"+name+"' is either not in our database or does not have any reviews in our database. Please try searching for something else."
        info.append(message1)
        context = dict(data = info)
        return render_template("error.html", **context)


    info.append("User Reviews for "+name+":")
    info.append(linebreak)

    query = text("""Select R.name, U.name, UW.review_date, UR.rating, UR.detail
                    From Restaurant R, User_Reviews UR, u_writes_for UW, Users U
                    WHERE R.name = '{}'
                    AND U.uid = UW.uid
                    AND UW.rid = R.rid
                    AND UW.urid = UR.urid;
                """.format(name))

    cursor = g.conn.execute(query)

    for result in cursor:
        message2 = "User name: " + result[1]
        message3 = "Review date: " + str(result[2]) + "; Rating: "+ str(result[3])
        message4 = "Review detail: "+ result[4]
        info.append(message2)
        info.append(message3)
        info.append(message4)
        info.append(linebreak)
    cursor.close()

    context = dict(data = info)

    return render_template("query.html", **context)



@app.route('/reviewquery', methods=['POST'])
def reviewquery():
    URdetail = str(request.form['URdetail'])
    info = []
    linebreak = "--------------------"

    query = text("""Select R.name
                    From Restaurant R, User_Reviews UR, u_writes_for UW
                    WHERE UR.detail LIKE '%{}%'
                    AND UW.rid = R.rid
                    AND UW.urid = UR.urid;
                """.format(URdetail))

    cursor = g.conn.execute(query)
    row = cursor.fetchone()
    info = []

    if row == None:
        cursor.close()
        message1 = "The input '"+URdetail+"' is not found in any reviews in our database. Please try searching for something else."
        info.append(message1)
        context = dict(data = info)
        return render_template("error.html", **context)

    info.append("User Reviews with keyword "+URdetail+":")
    info.append(linebreak)

    query = text("""Select R.name, U.name, UW.review_date, UR.rating, UR.detail
                    From Restaurant R, User_Reviews UR, u_writes_for UW, Users U
                    WHERE UR.detail LIKE '%{}%'
                    AND U.uid = UW.uid
                    AND UW.rid = R.rid
                    AND UW.urid = UR.urid
                    LIMIT 20;
                """.format(URdetail))

    cursor = g.conn.execute(query)

    for result in cursor:
        message1 = "Restaurant name: " + result[0]
        message2 = "User name: " + result[1]
        message3 = "Review date: " + str(result[2]) + "; Rating: "+ str(result[3])
        message4 = "Review detail: "+ result[4]
        info.append(message1)
        info.append(message2)
        info.append(message3)
        info.append(message4)
        info.append(linebreak)
    cursor.close()

    context = dict(data = info)

    return render_template("query.html", **context)


#
# This is an example of a different path.  You can see it at:
#
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
@app.route('/advquery')
def advquery():
  return render_template("advquery.html")

@app.route('/morequery',methods=['POST'])
def morequery():
    cat = str(request.form['category'])
    rating = float(request.form['rating'])
    option = str(request.form['option'])
    need = str(request.form['dietary'])
    info = []

    info.append("Restaurants that matches your input:")

    query = text("""SELECT R.name
                FROM Restaurant R, u_writes_for UW, User_Reviews UR, Satisfies S, offers O
                WHERE R.rid = UW.rid
                AND UW.urid = UR.urid
                AND R.rid = S.rid
                AND S.rid = O.rid
                AND R.category = '{}'
                AND S.name =  '{}'
                AND O.type = '{}'
                GROUP BY R.name
                HAVING AVG(UR.rating)>= {};
                """.format(cat, need, option, rating))

    cursor = g.conn.execute(query)

    for result in cursor:
        info.append(result["name"])
    cursor.close()

    context = dict(data = info)
    return render_template("advquery.html", **context)

@app.route('/review')
def review():
  return render_template("addreview.html")


# Example of adding new data to the database
# Example of adding new data to the database



@app.route('/addreview', methods=['POST'])
def addreview():
    from random import random
    RID=""
    UserID = str(request.form['UserID'])
    username = str(request.form['username'])
    Reviews = str(request.form['Reviews'])
    Rdate = request.form['ReviewDate']
    URID=int(10000*random())
    rating = int(request.form['rating'])
    restaurant=str(request.form['restaurant'])

    info = []

    query=text("""SELECT R.rid
                  FROM Restaurant R
                  WHERE R.name ILIKE '%{}%';""".format(restaurant))
    cursor = g.conn.execute(query)
    row = cursor.fetchone()
    if row == None:
        cursor.close()
        message = "The restaurant you want to review for ({}) is not in our database. Please check if you typed the name wrong or try reviewing for another restaurant.".format(restaurant)
        info.append(message)
        context = dict(data = info)
        return render_template("error.html", **context)
    else:
        RID = row['rid']



    try:
        g.conn.execute("INSERT INTO Users (uid, name) VALUES('{}', '{}')".format(UserID, username))
    except:
        pass
    try:
        g.conn.execute("INSERT INTO User_Reviews(urid,rating,detail) VALUES('{}','{}','{}')".format(URID,rating,Reviews))
    except:
        message = "Something went wrong, please contact xw2767@columbia.edu to figure out what went wrong:)"
        info.append(message)
        context = dict(data = info)
        return render_template("error.html", **context)
    try:
        g.conn.execute('INSERT INTO u_writes_for(uid,urid,rid,review_date) VALUES(%s,%s,%s,%s)',UserID,URID,RID,Rdate)
    except:
        message = "Something went wrong, please contact xw2767@columbia.edu to figure out what went wrong:)"
        info.append(message)
        context = dict(data = info)
        return render_template("error.html", **context)

    info = []
    message1 = "Restaurant name: " + restaurant
    message2 = "User name: " + username
    message3 = "Review date: " + Rdate + "; Rating: "+ str(rating)
    message4 = "Review detail: "+ Reviews
    info.append(message1)
    info.append(message2)
    info.append(message3)
    info.append(message4)

    context = dict(data = info)

    return render_template("success.html", **context)



if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
