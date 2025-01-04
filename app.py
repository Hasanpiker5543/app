from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os
import numpy as np  # Import numpy to handle NaN values

app = Flask(__name__)

# إعداد الاتصال بقاعدة بيانات MySQL (XAMPP)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/taoufik1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# نموذج الجدول في قاعدة البيانات
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sous_famille = db.Column(db.String(200))
    designation_article = db.Column(db.String(200))
    activite = db.Column(db.String(100))
    marque = db.Column(db.String(100))
    modele = db.Column(db.String(100))
    code_onee = db.Column(db.String(100))
    numero_de_serie = db.Column(db.String(100))
    affectataire_nom = db.Column(db.String(100))
    affectataire_matricule = db.Column(db.String(100))
    entite = db.Column(db.String(100))

# وظيفة تهيئة قاعدة البيانات
def init_db():
    with app.app_context():
        db.create_all()
        print("تم إنشاء الجداول بنجاح!")

# وظيفة تحميل البيانات من ملف Excel إلى قاعدة البيانات
def load_data_from_excel(file_path):
    if not os.path.exists(file_path):
        print(f"الملف {file_path} غير موجود.")
        return

    try:
        data = pd.read_excel(file_path)
        required_columns = ['Sous_famille', 'Designation_article', 'Activite', 'Marque', 'Modele',
                            'Code_ONEE', 'Numero_de_Serie', 'Nom_affectataire', 'Matricule_affectataire', 'Entite']

        # التحقق من الأعمدة المطلوبة
        if not set(required_columns).issubset(data.columns):
            raise ValueError("ملف Excel يفتقد بعض الأعمدة المطلوبة.")

        # إعادة تسمية الأعمدة لتتوافق مع قاعدة البيانات
        data = data[required_columns]
        data.columns = ['sous_famille', 'designation_article', 'activite', 'marque', 'modele',
                        'code_onee', 'numero_de_serie', 'affectataire_nom', 'affectataire_matricule', 'entite']

        # Fill NaN values with None
        data = data.where(pd.notnull(data), None)

        # إدخال البيانات إلى قاعدة البيانات within app context
        with app.app_context():
            for _, row in data.iterrows():
                # Check if the item already exists to avoid duplicates
                existing_item = Item.query.filter_by(
                    sous_famille=row['sous_famille'],
                    designation_article=row['designation_article']
                ).first()

                if existing_item is None:  # Only add if it doesn't exist
                    item = Item(
                        sous_famille=row['sous_famille'],
                        designation_article=row['designation_article'],
                        activite=row['activite'],
                        marque=row['marque'],
                        modele=row['modele'],
                        code_onee=row['code_onee'],
                        numero_de_serie=row['numero_de_serie'],
                        affectataire_nom=row['affectataire_nom'],
                        affectataire_matricule=row['affectataire_matricule'],
                        entite=row['entite']
                    )
                    db.session.add(item)
            db.session.commit()
            print("تم تحميل البيانات بنجاح!")
    except Exception as e:
        print(f"خطأ أثناء تحميل البيانات: {e}")
        db.session.rollback()  # Rollback in case of error

# المسارات (Routes)
@app.route('/')
def index():
    items = Item.query.all()
    return render_template('index.html', items=items)

@app.route('/add', methods=['POST'])
def add_item():
    # استخراج البيانات من النموذج، مع استبدال القيم الفارغة بـ None
    sous_famille = request.form.get('sous_famille') or None
    designation_article = request.form.get('designation_article') or None
    activite = request.form.get('activite') or None
    marque = request.form.get('marque') or None
    modele = request.form.get('modele') or None
    code_onee = request.form.get('code_onee') or None
    numero_de_serie = request.form.get('numero_de_serie') or None
    affectataire_nom = request.form.get('affectataire_nom') or None
    affectataire_matricule = request.form.get('affectataire_matricule') or None
    entite = request.form.get('entite') or None

    # إنشاء عنصر جديد
    item = Item(
        sous_famille=sous_famille,
        designation_article=designation_article,
        activite=activite,
        marque=marque,
        modele=modele,
        code_onee=code_onee,
        numero_de_serie=numero_de_serie,
        affectataire_nom=affectataire_nom,
        affectataire_matricule=affectataire_matricule,
        entite=entite
    )

    # التحقق من التكرار بناءً على بعض الحقول الأساسية فقط
    existing_item = Item.query.filter_by(
        sous_famille=item.sous_famille,
        designation_article=item.designation_article
    ).first()

    if existing_item is None:
        try:
            db.session.add(item)
            db.session.commit()
            print("تمت إضافة العنصر بنجاح!")
        except Exception as e:
            db.session.rollback()
            print(f"حدث خطأ أثناء الإضافة: {e}")
    else:
        print("العنصر موجود بالفعل، لن يتم الإضافة.")

    return redirect(url_for('index'))




@app.route('/delete/<int:item_id>')
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)

    if request.method == 'POST':
        item.sous_famille = request.form['sous_famille']
        item.designation_article = request.form['designation_article']
        item.activite = request.form['activite']
        item.marque = request.form['marque']
        item.modele = request.form['modele']
        item.code_onee = request.form['code_onee']
        item.numero_de_serie = request.form['numero_de_serie']
        item.affectataire_nom = request.form['affectataire_nom']
        item.affectataire_matricule = request.form['affectataire_matricule']
        item.entite = request.form['entite']

        db.session.commit()
        return redirect(url_for('index'))

    return render_template('edit.html', item=item)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    items = Item.query.filter(
        (Item.sous_famille.ilike(f'%{query}%')) |
        (Item.designation_article.ilike(f'%{query}%')) |
        (Item.activite.ilike(f'%{query}%')) |
        (Item.marque.ilike(f'%{query}%')) |
        (Item.modele.ilike(f'%{query}%')) |
        (Item.code_onee.ilike(f'%{query}%')) |
        (Item.numero_de_serie.ilike(f'%{query}%')) |
        (Item.affectataire_nom.ilike(f'%{query}%')) |
        (Item.affectataire_matricule.ilike(f'%{query}%')) |
        (Item.entite.ilike(f'%{query}%'))
    ).all()
    return render_template('index.html', items=items)

if __name__ == '__main__':
    # تهيئة قاعدة البيانات (إن لم تكن الجداول موجودة)
    init_db()

    # تحميل البيانات من ملف Excel
    load_data_from_excel('site.xlsx')

    # تشغيل التطبيق
    app.run(debug=True)
