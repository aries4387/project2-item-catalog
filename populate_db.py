
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Item, User, Base

engine = create_engine('sqlite:///itemcatalog.db')

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create users
user1 = User(id="none-1", name="Matt Mohan", email="matt123@gmail.com", profile_pic="")
session.add(user1)
session.commit()

user2 = User(id="none-2", name="Stella Sparks", email="stella345@gmail.com", profile_pic="")
session.add(user2)
session.commit()

# Create Categories
category1 = Category(name="Baby Clothing", user_id=user1.id)
session.add(category1)
session.commit()

category2 = Category(name="Diapers", user_id=user1.id)
session.add(category2)
session.commit()

category3 = Category(name="Toys", user_id=user2.id)
session.add(category3)
session.commit()

category4 = Category(name="Feeding", user_id=user2.id)
session.add(category4)
session.commit()

item1 = Item(title="Dresses", description="Find dresses for Girls from New born to 5 years old", category_id=category1.id, user_id=user1.id)
session.add(item1)
session.commit()

item2 = Item(title="Pajamas", description="Very comfortable night ware in different sizes and styles", category_id=category1.id, user_id=user1.id)
session.add(item2)
session.commit()

item3 = Item(title="SwimSuits", description="Summer is Here!! Find Different styles of swimsuits for Babies and toddlers", category_id=category1.id, user_id=user1.id)
session.add(item3)
session.commit()

item4 = Item(title="Cloth Diapers", description="Organic cotton cloth diapers are very gentle to Baby's soft and sensitive skin", category_id=category2.id, user_id=user1.id)
session.add(item4)
session.commit()

item5 = Item(title="Diaper Bag", description="Fits all the baby items you need, different styles and size available", category_id=category2.id, user_id=user1.id)
session.add(item5)
session.commit()

item6 = Item(title="Diaper Cream", description="Helps heal diaper rashes and also prevents rashes if used regularly", category_id=category2.id, user_id=user1.id)
session.add(item6)
session.commit()

item7 = Item(title="Learning Toys", description="find varieties of toys to improve baby's moter skills", category_id=category3.id, user_id=user2.id)
session.add(item7)
session.commit()

item8 = Item(title="Bath Toys", description="makr bathing fun with cool bath toys like ships,ducks and fishes", category_id=category3.id, user_id=user2.id)
session.add(item8)
session.commit()

item9 = Item(title="Sports Toys", description="kids sports game sets like baseball, basketball, soccer and football", category_id=category3.id, user_id=user2.id)
session.add(item9)
session.commit()

item10 = Item(title="Baby Food", description="Organic baby food items and yogurt", category_id=category4.id, user_id=user2.id)
session.add(item10)
session.commit()

item11 = Item(title="Formula", description="Different types of flavors of formuls for healthy baby", category_id=category4.id, user_id=user2.id)
session.add(item11)
session.commit()

item12 = Item(title="Bottles", description="FDA approved bottles with easy grip and soft tip", category_id=category4.id, user_id=user2.id)
session.add(item12)
session.commit()
