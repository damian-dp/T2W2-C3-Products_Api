from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

app = Flask(__name__)

# connect to database                     dbms     db_driver db_user  db_pass   URL     PORT db_name
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://feb_db_user:1234@localhost:5432/feb_db"

db = SQLAlchemy(app)
ma = Marshmallow(app)

# Model - table
class Product(db.Model):
    # define the tablename
    __tablename__ = "products"
    # define the primary key
    id = db.Column(db.Integer, primary_key=True)
    # more attributes (columns)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String)
    price = db.Column(db.Float)
    stock = db.Column(db.Integer)

# Schema
class ProductSchema(ma.Schema):
    class Meta:
        # fields to be serialized
        fields = ("id", "name", "description", "price", "stock")
        
# create an instance of the schema to handle multiple products
products_schema = ProductSchema(many=True)

# create an instance of the schema to handle a single product
product_schema = ProductSchema()



# CLI Commands
@app.cli.command("create")
def create_tables():
    db.create_all()
    print("Tables created")


@app.cli.command("seed")
def seed_tables():
    # create a product object
    product1 = Product(
        name="Product 1",
        description="Product 1 description",
        price=479.99,
        stock=15
    )

    product2 = Product()
    product2.name = "Product 2"
    product2.price = 15.99
    product2.stock = 24

    # products = [product1, product2]
    # db.session.add_all(products)

    # add to session
    db.session.add(product1)
    db.session.add(product2)

    # commit
    db.session.commit()

    print("Tables seeded")


@app.cli.command("drop")
def drop_tables():
    db.drop_all()
    print("Tables dropped")
    


# /products, GET => get all products
# /products/<id>, GET => get a single product where id is = to the one in the URL
# /products, POST => create a new product
# /products/<id>, PUT/PATCH => edit/update a product where id is = to the one in the URL
# /products/<id>, DELETE => delete a product where id is = to the one in the URL


# Get all products
@app.route("/products")
def get_products():
    # SELECT * FROM products
    stmt = db.select(Product) # Result [[Product1], [Product2]]
    products_list = db.session.scalars(stmt) # ScalarResult [Product1, Product2]
    data = products_schema.dump(products_list)
    return data


# Get a single product
@app.route("/products/<int:product_id>")
def get_product(product_id):
    # SELECT * FROM products WHERE id = id
    stmt = db.select(Product).filter_by(id = product_id)
    product = db.session.scalar(stmt)
    if product:
        data = product_schema.dump(product)
        return data
    else:
        return {"error": f"Product with id {product_id} does not exist"}, 404
    

# Create a product
@app.route("/products", methods=["POST"])
def create_product():
    product_fields = request.get_json()
    # create a product object/model using the data from the request body
    new_product = Product(
        name=product_fields.get("name"),
        description=product_fields.get("description"),
        price=product_fields.get("price"),
        stock=product_fields.get("stock")
    )
    
    # add to session
    db.session.add(new_product)
    
    # commit
    db.session.commit()
    
    return product_schema.dump(new_product), 201


# Update a product
@app.route("/products/<int:product_id>", methods=["PUT", "PATCH"])
def update_product(product_id):
    
    # Find the product from the database with the id from the URL
    stmt = db.select(Product).filter_by(id=product_id) # SELECT * FROM products WHERE id = product_id
    product = db.session.scalar(stmt) 
    
    # Retrieve the data from the request body
    body = request.get_json()
    
    # Check if the product exists
    if product:
        # Update the product object with the new data
        product.name = body.get("name") or product.name                             # Update the product name if it exists in the request body otherwise keep the old name
        product.description = body.get("description") or product.description        # Update the product description if it exists in the request body otherwise keep the old description
        product.stock = body.get("stock") or product.stock                          # Update the product stock if it exists in the request body otherwise keep the old stock
        product.price = body.get("price") or product.price                          # Update the product price if it exists in the request body otherwise keep the old price
        
        # commit the changes
        db.session.commit()                                                         # Add the updated product to the database
        
        #return the updated product
        return product_schema.dump(product)                                         # Return the updated product as a response to the client
    
    # If the product does not exist
    else:
        return {"error": f"Product with id {product_id} does not exist"}, 404
    

# DELETE a product 
@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    
    # Find the product from the database with the id from the URL
    stmt = db.select(Product).where(Product.id == product_id)                       # SELECT * FROM products WHERE id = product_id
    product = db.session.scalar(stmt)                                               
    
    # Check if the product exists
    if product:
        db.session.delete(product)                                                  # Delete the product from the database
        db.session.commit()                                                         # Commit the changes
        
        return {"message": f"Product with id {product_id} has been deleted"}        # Return a success message
    
    else:
        return {"error": f"Product with id {product_id} does not exist"}, 404       # Return an error message if the product does not exist