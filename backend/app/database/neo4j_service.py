import uuid
import hashlib
import hmac
import secrets
from datetime import date
from neo4j import GraphDatabase
from neo4j.time import Date
from backend.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE

def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return pwd_hash, salt

def verify_password(password: str, pwd_hash: str, salt: str) -> bool:
    expected_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(pwd_hash, expected_hash)

def convert_dates(data):
    if isinstance(data, dict):
        return {
            key: convert_dates(value)
            for key, value in data.items()
        }

    if isinstance(data, list):
        return [
            convert_dates(item)
            for item in data
        ]

    if isinstance(data, Date):
        return data.iso_format()

    return data

class Neo4jService:

    def __init__(self, database=None):
        self.database = database or NEO4J_DATABASE
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )

    # ---------------------------------------------------------
    # Context Retrieval Methods
    # ---------------------------------------------------------

    def get_financial_context(self, user_id="U001"):
        query = """
        MATCH (u:User {id: $user_id})

        CALL (u) {
            OPTIONAL MATCH (u)-[:HAS_ACCOUNT]->(a:Account)
            OPTIONAL MATCH (a)-[:MADE_TRANSACTION]->(t:Transaction)
            OPTIONAL MATCH (t)-[:BELONGS_TO]->(c:Category)

            RETURN collect(DISTINCT {
                id: a.id,
                bank: a.bank,
                type: a.account_type,
                balance: a.balance
            }) AS accounts,

            collect(DISTINCT {
                id: t.id,
                description: t.description,
                amount: t.amount,
                type: t.type,
                date: t.date,
                category: c.name
            }) AS transactions
        }

        CALL (u) {
            OPTIONAL MATCH (u)-[:RECEIVED_INCOME]->(i:Income)

            RETURN collect(DISTINCT {
                id: i.id,
                source: i.source,
                amount: i.amount,
                date: i.date
            }) AS incomes
        }

        CALL (u) {
            OPTIONAL MATCH (u)-[:HAS_LOAN]->(l:Loan)-[:HAS_EMI]->(e:EMI)

            RETURN collect(DISTINCT {
                loan_id: l.id,
                loan: l.name,
                outstanding: l.outstanding,
                emi_id: e.id,
                emi: e.amount,
                due_date: e.due_date,
                status: e.status
            }) AS loans
        }

        CALL (u) {
            OPTIONAL MATCH (u)-[:HAS_GOAL]->(g:Goal)

            RETURN collect(DISTINCT {
                id: g.id,
                name: g.name,
                target: g.target_amount,
                current: g.current_amount,
                target_date: g.target_date
            }) AS goals
        }

        RETURN {
            user: u.name,
            accounts: accounts,
            transactions: [t IN transactions WHERE t.id IS NOT NULL],
            incomes: [i IN incomes WHERE i.source IS NOT NULL],
            loans: [l IN loans WHERE l.loan IS NOT NULL],
            goals: [g IN goals WHERE g.name IS NOT NULL]
        } AS financial_context
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(query, user_id=user_id)
            record = result.single()

            if record:
                context = record["financial_context"]
                return convert_dates(context)

            return None

    def get_purchase_context(self, user_id="U001"):
        query = """
        MATCH (u:User {id: $user_id})

        OPTIONAL MATCH (u)-[:HAS_ACCOUNT]->(a:Account)
        OPTIONAL MATCH (u)-[:HAS_LOAN]->(l:Loan)-[:HAS_EMI]->(e:EMI)
        OPTIONAL MATCH (u)-[:HAS_ACCOUNT]->(a2:Account)-[:MADE_TRANSACTION]->(t:Transaction)
        OPTIONAL MATCH (t)-[:BELONGS_TO]->(c:Category)
        OPTIONAL MATCH (u)-[:HAS_GOAL]->(g:Goal)

        RETURN
            u.name AS user,

            collect(DISTINCT {
                account: a.id,
                balance: a.balance
            }) AS accounts,

            collect(DISTINCT {
                loan: l.name,
                emi: e.amount,
                due_date: e.due_date,
                status: e.status
            }) AS loans,

            collect(DISTINCT {
                transaction: t.description,
                amount: t.amount,
                type: t.type,
                category: c.name,
                date: t.date
            }) AS transactions,

            collect(DISTINCT {
                goal: g.name,
                target: g.target_amount,
                current: g.current_amount
            }) AS goals
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(query, user_id=user_id)
            record = result.single()

            if record:
                return convert_dates({
                    "user": record["user"],
                    "accounts": [a for a in record["accounts"] if a.get("account") is not None],
                    "loans": [l for l in record["loans"] if l.get("loan") is not None],
                    "transactions": [t for t in record["transactions"] if t.get("transaction") is not None],
                    "goals": [g for g in record["goals"] if g.get("goal") is not None]
                })

            return None

    def get_savings_context(self, user_id="U001"):
        query = """
        MATCH (u:User {id: $user_id})

        OPTIONAL MATCH (u)-[:RECEIVED_INCOME]->(i:Income)
        OPTIONAL MATCH (u)-[:HAS_ACCOUNT]->(a:Account)-[:MADE_TRANSACTION]->(t:Transaction)

        RETURN
            u.name AS user,

            collect(DISTINCT {
                source: i.source,
                amount: i.amount,
                date: i.date
            }) AS incomes,

            collect(DISTINCT {
                transaction: t.description,
                amount: t.amount,
                type: t.type,
                date: t.date
            }) AS transactions
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(query, user_id=user_id)
            record = result.single()

            if record:
                return convert_dates({
                    "user": record["user"],
                    "incomes": [i for i in record["incomes"] if i.get("source") is not None],
                    "transactions": [t for t in record["transactions"] if t.get("transaction") is not None]
                })

            return None
        
    def get_emergency_fund_context(self, user_id="U001"):
        query = """
        MATCH (u:User {id: $user_id})

        OPTIONAL MATCH (u)-[:HAS_ACCOUNT]->(a:Account)-[:MADE_TRANSACTION]->(t:Transaction)
        OPTIONAL MATCH (u)-[:HAS_GOAL]->(g:Goal)

        RETURN
            u.name AS user,

            collect(DISTINCT {
                transaction: t.description,
                amount: t.amount,
                type: t.type,
                date: t.date
            }) AS transactions,

            collect(DISTINCT {
                goal: g.name,
                target: g.target_amount,
                current: g.current_amount,
                target_date: g.target_date
            }) AS goals
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(query, user_id=user_id)
            record = result.single()

            if record:
                return convert_dates({
                    "user": record["user"],
                    "transactions": [t for t in record["transactions"] if t.get("transaction") is not None],
                    "goals": [g for g in record["goals"] if g.get("goal") is not None]
                })

            return None

    def get_summary_context(self, user_id="U001"):
        query = """
        MATCH (u:User {id: $user_id})

        OPTIONAL MATCH (u)-[:RECEIVED_INCOME]->(i:Income)
        OPTIONAL MATCH (u)-[:HAS_ACCOUNT]->(a:Account)
        OPTIONAL MATCH (a)-[:MADE_TRANSACTION]->(t:Transaction)
        OPTIONAL MATCH (u)-[:HAS_GOAL]->(g:Goal)

        RETURN
            u.name AS user,

            collect(DISTINCT {
                source: i.source,
                amount: i.amount,
                date: i.date
            }) AS incomes,

            collect(DISTINCT {
                account: a.id,
                balance: a.balance
            }) AS accounts,

            collect(DISTINCT {
                transaction: t.description,
                amount: t.amount,
                type: t.type,
                date: t.date
            }) AS transactions,

            collect(DISTINCT {
                goal: g.name,
                target: g.target_amount,
                current: g.current_amount,
                target_date: g.target_date
            }) AS goals
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(query, user_id=user_id)
            record = result.single()

            if record:
                return convert_dates({
                    "user": record["user"],
                    "incomes": [i for i in record["incomes"] if i.get("source") is not None],
                    "accounts": [a for a in record["accounts"] if a.get("account") is not None],
                    "transactions": [t for t in record["transactions"] if t.get("transaction") is not None],
                    "goals": [g for g in record["goals"] if g.get("goal") is not None]
                })

            return None

    # ---------------------------------------------------------
    # Helper & Inquiry Methods
    # ---------------------------------------------------------

    def get_user_accounts(self, user_id="U001"):
        query = """
        MATCH (u:User {id: $user_id})-[:HAS_ACCOUNT]->(a:Account)
        RETURN a.id AS id, a.bank AS bank, a.account_type AS account_type, a.balance AS balance
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, user_id=user_id)
            return [dict(record) for record in result]

    def get_all_transactions(self, user_id="U001", limit=100):
        limit = max(1, min(1000, int(limit)))
        query = """
        MATCH (u:User {id: $user_id})-[:HAS_ACCOUNT]->(a:Account)-[:MADE_TRANSACTION]->(t:Transaction)
        OPTIONAL MATCH (t)-[:BELONGS_TO]->(c:Category)
        RETURN t.id AS id, t.description AS description, t.amount AS amount,
               t.type AS type, t.date AS date, c.name AS category, a.id AS account_id, a.bank AS bank
        ORDER BY t.date DESC
        LIMIT $limit
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, user_id=user_id, limit=limit)
            return convert_dates([dict(record) for record in result])

    def get_categories(self):
        query = """
        MATCH (c:Category)
        RETURN c.id AS id, c.name AS name
        ORDER BY c.name ASC
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query)
            return [dict(record) for record in result]

    # ---------------------------------------------------------
    # Dynamic Knowledge Graph CRUD Operations (Phase 1)
    # ---------------------------------------------------------

    def add_transaction(self, user_id="U001", account_id=None, amount=0, description="", category_name="General", transaction_type="EXPENSE", date_str=None):
        if amount <= 0:
            raise ValueError(f"Transaction amount must be positive. Received: {amount}")

        if not date_str:
            date_str = date.today().isoformat()

        if not account_id:
            accounts = self.get_user_accounts(user_id)
            if not accounts:
                raise ValueError(f"No account found for user {user_id}")
            account_id = accounts[0]["id"]

        category_name = category_name.strip().title() if category_name else "General"
        transaction_id = f"T_{uuid.uuid4().hex[:8].upper()}"
        category_id = f"C_{uuid.uuid4().hex[:6].upper()}"

        query = """
        MATCH (u:User {id: $user_id})-[:HAS_ACCOUNT]->(a:Account {id: $account_id})
        MERGE (c:Category {name: $category_name})
          ON CREATE SET c.id = $category_id

        CREATE (t:Transaction {
            id: $transaction_id,
            description: $description,
            amount: $amount,
            type: $transaction_type,
            date: date($date_str)
        })

        CREATE (a)-[:MADE_TRANSACTION]->(t)
        CREATE (t)-[:BELONGS_TO]->(c)

        SET a.balance = a.balance + (CASE WHEN $transaction_type = 'INCOME' THEN $amount ELSE -$amount END)

        RETURN t.id AS transaction_id,
               t.description AS description,
               t.amount AS amount,
               t.type AS type,
               t.date AS date,
               c.name AS category,
               a.id AS account_id,
               a.balance AS new_balance
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(
                query,
                user_id=user_id,
                account_id=account_id,
                category_name=category_name,
                category_id=category_id,
                transaction_id=transaction_id,
                description=description,
                amount=amount,
                transaction_type=transaction_type,
                date_str=date_str
            )
            record = result.single()
            if not record:
                raise ValueError(f"Failed to add transaction for user {user_id} and account {account_id}")

            return convert_dates(dict(record))

    def update_transaction(self, user_id, transaction_id, amount=None, description=None, category_name=None, date_str=None):
        find_query = """
        MATCH (u:User {id: $user_id})-[:HAS_ACCOUNT]->(a:Account)-[:MADE_TRANSACTION]->(t:Transaction {id: $transaction_id})
        OPTIONAL MATCH (t)-[r:BELONGS_TO]->(c:Category)
        RETURN t.amount AS old_amount, t.type AS type, a.id AS account_id, c.name AS old_category
        """
        with self.driver.session(database=self.database) as session:
            res = session.run(find_query, user_id=user_id, transaction_id=transaction_id).single()
            if not res:
                raise ValueError(f"Transaction with id '{transaction_id}' not found")
            old_amount = res["old_amount"]
            tx_type = res["type"]
            account_id = res["account_id"]

        amount_diff = 0
        if amount is not None:
            if amount <= 0:
                raise ValueError(f"Updated amount must be positive. Received: {amount}")
            amount_diff = amount - old_amount

        category_id = f"C_{uuid.uuid4().hex[:6].upper()}"

        update_query = """
        MATCH (u:User {id: $user_id})-[:HAS_ACCOUNT]->(a:Account {id: $account_id})-[:MADE_TRANSACTION]->(t:Transaction {id: $transaction_id})
        
        SET t.amount = CASE WHEN $amount IS NOT NULL THEN $amount ELSE t.amount END,
            t.description = CASE WHEN $description IS NOT NULL THEN $description ELSE t.description END,
            t.date = CASE WHEN $date_str IS NOT NULL THEN date($date_str) ELSE t.date END

        SET a.balance = a.balance - (CASE WHEN $tx_type = 'EXPENSE' THEN $amount_diff ELSE -$amount_diff END)

        WITH t, a
        CALL (t) {
            WITH t
            WHERE $category_name IS NOT NULL
            OPTIONAL MATCH (t)-[old_rel:BELONGS_TO]->(:Category)
            DELETE old_rel
            WITH t
            MERGE (new_c:Category {name: $category_name})
              ON CREATE SET new_c.id = $category_id
            MERGE (t)-[:BELONGS_TO]->(new_c)
            RETURN new_c.name AS final_category
        }

        OPTIONAL MATCH (t)-[:BELONGS_TO]->(c_current:Category)
        RETURN t.id AS transaction_id,
               t.description AS description,
               t.amount AS amount,
               t.type AS type,
               t.date AS date,
               c_current.name AS category,
               a.id AS account_id,
               a.balance AS new_balance
        """

        category_clean = category_name.strip().title() if category_name else None

        with self.driver.session(database=self.database) as session:
            result = session.run(
                update_query,
                transaction_id=transaction_id,
                user_id=user_id,
                account_id=account_id,
                amount=amount,
                amount_diff=amount_diff,
                tx_type=tx_type,
                description=description,
                date_str=date_str,
                category_name=category_clean,
                category_id=category_id
            )
            record = result.single()
            return convert_dates(dict(record))

    def delete_transaction(self, user_id, transaction_id):
        query = """
        MATCH (u:User {id: $user_id})-[:HAS_ACCOUNT]->(a:Account)-[:MADE_TRANSACTION]->(t:Transaction {id: $transaction_id})
        WITH a, t, t.amount AS amount, t.type AS type
        SET a.balance = a.balance + (CASE WHEN type = 'EXPENSE' THEN amount ELSE -amount END)
        DETACH DELETE t
        RETURN a.id AS account_id, a.balance AS restored_balance
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, user_id=user_id, transaction_id=transaction_id)
            record = result.single()
            if not record:
                raise ValueError(f"Transaction with id '{transaction_id}' not found")
            return dict(record)

    def add_income(self, user_id="U001", source="Salary", amount=0, date_str=None, account_id=None):
        if amount <= 0:
            raise ValueError(f"Income amount must be positive. Received: {amount}")

        if not date_str:
            date_str = date.today().isoformat()

        income_id = f"I_{uuid.uuid4().hex[:8].upper()}"

        query = """
        MATCH (u:User {id: $user_id})
        CREATE (i:Income {
            id: $income_id,
            source: $source,
            amount: $amount,
            date: date($date_str)
        })
        CREATE (u)-[:RECEIVED_INCOME]->(i)

        WITH u, i
        OPTIONAL MATCH (u)-[:HAS_ACCOUNT]->(a:Account {id: $account_id})
        FOREACH (_ IN CASE WHEN a IS NOT NULL THEN [1] ELSE [] END |
            SET a.balance = a.balance + $amount
        )

        RETURN i.id AS income_id, i.source AS source, i.amount AS amount, i.date AS date
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(
                query,
                user_id=user_id,
                income_id=income_id,
                source=source,
                amount=amount,
                date_str=date_str,
                account_id=account_id
            )
            record = result.single()
            return convert_dates(dict(record))

    def add_or_update_goal(self, user_id="U001", name="Emergency Fund", target_amount=100000, current_amount=None, target_date=None):
        goal_id = f"G_{uuid.uuid4().hex[:8].upper()}"
        query = """
        MATCH (u:User {id: $user_id})
        MERGE (u)-[:HAS_GOAL]->(g:Goal {name: $name})
          ON CREATE SET g.id = $goal_id,
                        g.target_amount = $target_amount,
                        g.current_amount = coalesce($current_amount, 0),
                        g.target_date = CASE WHEN $target_date IS NOT NULL THEN date($target_date) ELSE date('2027-01-01') END
          ON MATCH SET g.target_amount = $target_amount,
                       g.current_amount = CASE WHEN $current_amount IS NOT NULL THEN $current_amount ELSE g.current_amount END,
                       g.target_date = CASE WHEN $target_date IS NOT NULL THEN date($target_date) ELSE g.target_date END
        RETURN g.id AS id, g.name AS name, g.target_amount AS target_amount, g.current_amount AS current_amount, g.target_date AS target_date
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(
                query,
                user_id=user_id,
                goal_id=goal_id,
                name=name,
                target_amount=target_amount,
                current_amount=current_amount,
                target_date=target_date
            )
            record = result.single()
            return convert_dates(dict(record))

    def add_loan(self, user_id="U001", name="Personal Loan", principal=0, outstanding=0):
        loan_id = f"L_{uuid.uuid4().hex[:8].upper()}"
        query = """
        MATCH (u:User {id: $user_id})
        CREATE (l:Loan {
            id: $loan_id,
            name: $name,
            principal: $principal,
            outstanding: $outstanding
        })
        CREATE (u)-[:HAS_LOAN]->(l)
        RETURN l.id AS id, l.name AS name, l.principal AS principal, l.outstanding AS outstanding
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(
                query,
                user_id=user_id,
                loan_id=loan_id,
                name=name,
                principal=principal,
                outstanding=outstanding
            )
            record = result.single()
            return dict(record)

    def add_emi(self, loan_id, amount=0, due_date=None, status="PENDING"):
        emi_id = f"E_{uuid.uuid4().hex[:8].upper()}"
        if not due_date:
            due_date = date.today().isoformat()

        query = """
        MATCH (l:Loan {id: $loan_id})
        CREATE (e:EMI {
            id: $emi_id,
            amount: $amount,
            due_date: date($due_date),
            status: $status
        })
        CREATE (l)-[:HAS_EMI]->(e)
        RETURN e.id AS id, e.amount AS amount, e.due_date AS due_date, e.status AS status
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(
                query,
                loan_id=loan_id,
                emi_id=emi_id,
                amount=amount,
                due_date=due_date,
                status=status
            )
            record = result.single()
            return convert_dates(dict(record))

    def update_emi_status(self, emi_id, status="PAID", account_id=None):
        query = """
        MATCH (e:EMI {id: $emi_id})
        SET e.status = $status
        WITH e
        OPTIONAL MATCH (a:Account {id: $account_id})
        FOREACH (_ IN CASE WHEN a IS NOT NULL AND $status = 'PAID' THEN [1] ELSE [] END |
            SET a.balance = a.balance - e.amount
        )
        RETURN e.id AS id, e.amount AS amount, e.status AS status
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, emi_id=emi_id, status=status, account_id=account_id)
            record = result.single()
            return dict(record)

    def update_account_balance(self, account_id, new_balance):
        query = """
        MATCH (a:Account {id: $account_id})
        SET a.balance = $new_balance
        RETURN a.id AS id, a.bank AS bank, a.balance AS balance
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, account_id=account_id, new_balance=new_balance)
            record = result.single()
            return dict(record)

    def create_user(self, username, password, name=None, initial_balance=0.0, bank_name="Primary Bank"):
        clean_username = username.strip().lower()
        display_name = name.strip() if name and name.strip() else clean_username.capitalize()
        pwd_hash, salt = hash_password(password)
        user_id = f"U_{uuid.uuid4().hex[:8].upper()}"
        account_id = f"A_{uuid.uuid4().hex[:8].upper()}"

        check_query = "MATCH (u:User) WHERE toLower(u.username) = $username RETURN u.id AS id"
        with self.driver.session(database=self.database) as session:
            existing = session.run(check_query, username=clean_username).single()
            if existing:
                raise ValueError("Username already exists")

            create_query = """
            CREATE (u:User {
                id: $user_id,
                username: $username,
                name: $name,
                password_hash: $pwd_hash,
                salt: $salt,
                created_at: date()
            })
            CREATE (a:Account {
                id: $account_id,
                bank: $bank_name,
                account_type: 'Savings',
                balance: $initial_balance
            })
            CREATE (u)-[:HAS_ACCOUNT]->(a)

            MERGE (c1:Category {name: 'Housing'}) ON CREATE SET c1.id = 'C001'
            MERGE (c2:Category {name: 'Food'}) ON CREATE SET c2.id = 'C002'
            MERGE (c3:Category {name: 'Transport'}) ON CREATE SET c3.id = 'C003'
            MERGE (c4:Category {name: 'Utilities'}) ON CREATE SET c4.id = 'C004'
            MERGE (c5:Category {name: 'Shopping'}) ON CREATE SET c5.id = 'C005'
            MERGE (c6:Category {name: 'Healthcare'}) ON CREATE SET c6.id = 'C006'
            MERGE (c7:Category {name: 'Entertainment'}) ON CREATE SET c7.id = 'C007'

            RETURN u.id AS user_id, u.username AS username, u.name AS name, a.id AS account_id, a.balance AS balance
            """
            result = session.run(
                create_query,
                user_id=user_id,
                username=clean_username,
                name=display_name,
                pwd_hash=pwd_hash,
                salt=salt,
                account_id=account_id,
                bank_name=bank_name,
                initial_balance=float(initial_balance)
            )
            record = result.single()
            return dict(record)

    def authenticate_user(self, username, password):
        clean_username = username.strip().lower()
        query = """
        MATCH (u:User)
        WHERE toLower(u.username) = $username OR toLower(u.name) = $username
        RETURN u.id AS user_id, u.username AS username, u.name AS name, u.password_hash AS password_hash, u.salt AS salt
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, username=clean_username)
            record = result.single()
            if not record:
                return None
            user = dict(record)
            if user.get("password_hash") and user.get("salt"):
                if verify_password(password, user["password_hash"], user["salt"]):
                    return {
                        "user_id": user["user_id"],
                        "username": user.get("username") or user["name"],
                        "name": user["name"]
                    }
                return None
            return None

    def get_user_by_id(self, user_id):
        query = """
        MATCH (u:User {id: $user_id})
        RETURN u.id AS user_id, u.username AS username, u.name AS name
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, user_id=user_id)
            record = result.single()
            if record:
                return dict(record)
            return None

    # ---------------------------------------------------------
    # Portfolio & Investment Operations
    # ---------------------------------------------------------

    def init_portfolio_constraints(self):
        queries = [
            "CREATE CONSTRAINT asset_symbol_uniq IF NOT EXISTS FOR (a:Asset) REQUIRE a.symbol IS UNIQUE",
            "CREATE CONSTRAINT portfolio_id_uniq IF NOT EXISTS FOR (p:Portfolio) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT holding_id_uniq IF NOT EXISTS FOR (h:Holding) REQUIRE h.id IS UNIQUE",
            "CREATE CONSTRAINT inv_tx_id_uniq IF NOT EXISTS FOR (it:InvestmentTransaction) REQUIRE it.id IS UNIQUE"
        ]
        with self.driver.session(database=self.database) as session:
            for q in queries:
                try:
                    session.run(q)
                except Exception:
                    pass

    def get_user_portfolio(self, user_id="U001"):
        query = """
        MATCH (u:User {id: $user_id})
        MERGE (u)-[:OWNS_PORTFOLIO]->(p:Portfolio)
          ON CREATE SET p.id = 'P_' + $user_id, p.name = 'Primary Portfolio', p.created_at = date()
        
        OPTIONAL MATCH (p)-[:HAS_HOLDING]->(h:Holding)-[:OF_ASSET]->(a:Asset)
        WHERE h.quantity > 0
        OPTIONAL MATCH (h)-[:HAS_INVESTMENT_TRANSACTION]->(it:InvestmentTransaction)
        
        WITH p, h, a, it
        ORDER BY it.date DESC
        
        WITH p, h, a, collect(DISTINCT {
            id: it.id,
            type: it.type,
            quantity: it.quantity,
            price: it.price,
            total_amount: it.total_amount,
            date: it.date,
            notes: it.notes
        }) AS txs
        
        WITH p, collect(DISTINCT CASE WHEN h IS NOT NULL THEN {
            id: h.id,
            symbol: a.symbol,
            name: a.name,
            asset_type: a.asset_type,
            currency: a.currency,
            quantity: h.quantity,
            average_cost: h.average_cost,
            notes: h.notes,
            transactions: [t IN txs WHERE t.id IS NOT NULL]
        } ELSE NULL END) AS raw_holdings
        
        RETURN {
            portfolio_id: p.id,
            name: p.name,
            holdings: [h IN raw_holdings WHERE h IS NOT NULL]
        } AS portfolio
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, user_id=user_id)
            record = result.single()
            if record and record["portfolio"]:
                return convert_dates(record["portfolio"])
            return {"portfolio_id": f"P_{user_id}", "name": "Primary Portfolio", "holdings": []}

    def add_investment_transaction(self, user_id, symbol, name, asset_type="STOCK", transaction_type="BUY", quantity=0.0, price=0.0, date_str=None, account_id=None, notes=None):
        if quantity <= 0 or price <= 0:
            raise ValueError("Quantity and price must be positive numbers")

        symbol = symbol.strip().upper()
        name = name.strip() if name else symbol
        asset_type = asset_type.strip().upper() if asset_type else "STOCK"
        transaction_type = transaction_type.strip().upper() if transaction_type else "BUY"
        date_str = date_str or date.today().isoformat()
        total_amount = round(quantity * price, 2)
        inv_tx_id = f"IT_{uuid.uuid4().hex[:8].upper()}"
        holding_id = f"H_{uuid.uuid4().hex[:8].upper()}"

        query = """
        MATCH (u:User {id: $user_id})
        MERGE (u)-[:OWNS_PORTFOLIO]->(p:Portfolio)
          ON CREATE SET p.id = 'P_' + $user_id, p.name = 'Primary Portfolio', p.created_at = date()

        MERGE (a:Asset {symbol: $symbol})
          ON CREATE SET a.name = $name, a.asset_type = $asset_type, a.currency = 'INR'
          ON MATCH SET a.name = coalesce($name, a.name), a.asset_type = coalesce($asset_type, a.asset_type)

        // Find or create holding
        MERGE (p)-[:HAS_HOLDING]->(h:Holding)-[:OF_ASSET]->(a)
          ON CREATE SET h.id = $holding_id,
                        h.quantity = CASE WHEN $transaction_type = 'BUY' THEN $quantity ELSE 0 END,
                        h.average_cost = CASE WHEN $transaction_type = 'BUY' THEN $price ELSE 0 END,
                        h.notes = $notes,
                        h.updated_at = date($date_str)
          ON MATCH SET
            h.average_cost = CASE
                WHEN $transaction_type = 'BUY' AND (h.quantity + $quantity) > 0
                THEN ((h.quantity * h.average_cost) + ($quantity * $price)) / (h.quantity + $quantity)
                ELSE h.average_cost
            END,
            h.quantity = CASE
                WHEN $transaction_type = 'BUY' THEN h.quantity + $quantity
                WHEN $transaction_type = 'SELL' AND (h.quantity - $quantity) > 0 THEN h.quantity - $quantity
                WHEN $transaction_type = 'SELL' THEN 0.0
                ELSE h.quantity
            END,
            h.updated_at = date($date_str)

        // Create investment transaction record
        CREATE (it:InvestmentTransaction {
            id: $inv_tx_id,
            type: $transaction_type,
            quantity: $quantity,
            price: $price,
            total_amount: $total_amount,
            date: date($date_str),
            notes: $notes
        })
        CREATE (h)-[:HAS_INVESTMENT_TRANSACTION]->(it)

        // Adjust cash balance in designated bank account atomically
        WITH u, h, a, it
        OPTIONAL MATCH (u)-[:HAS_ACCOUNT]->(acc:Account {id: $account_id})
        FOREACH (_ IN CASE WHEN acc IS NOT NULL AND $transaction_type = 'BUY' THEN [1] ELSE [] END |
            SET acc.balance = acc.balance - $total_amount
        )
        FOREACH (_ IN CASE WHEN acc IS NOT NULL AND $transaction_type = 'SELL' THEN [1] ELSE [] END |
            SET acc.balance = acc.balance + $total_amount
        )

        RETURN h.id AS holding_id,
               a.symbol AS symbol,
               a.name AS name,
               a.asset_type AS asset_type,
               h.quantity AS new_quantity,
               h.average_cost AS new_average_cost,
               it.id AS transaction_id,
               it.type AS transaction_type,
               it.total_amount AS total_amount,
               acc.id AS account_id,
               acc.balance AS new_account_balance
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(
                query,
                user_id=user_id,
                symbol=symbol,
                name=name,
                asset_type=asset_type,
                transaction_type=transaction_type,
                quantity=float(quantity),
                price=float(price),
                total_amount=float(total_amount),
                date_str=date_str,
                holding_id=holding_id,
                inv_tx_id=inv_tx_id,
                account_id=account_id,
                notes=notes
            )
            record = result.single()
            if not record:
                raise ValueError("Failed to execute investment transaction")
            return convert_dates(dict(record))

    def delete_holding(self, user_id, holding_id):
        query = """
        MATCH (u:User {id: $user_id})-[:OWNS_PORTFOLIO]->(p:Portfolio)-[:HAS_HOLDING]->(h:Holding {id: $holding_id})
        OPTIONAL MATCH (h)-[:HAS_INVESTMENT_TRANSACTION]->(it:InvestmentTransaction)
        DETACH DELETE it, h
        RETURN count(h) AS deleted_count
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, user_id=user_id, holding_id=holding_id)
            record = result.single()
            return {"deleted": record["deleted_count"] > 0}

    def get_watchlist(self, user_id="U001"):
        query = """
        MATCH (u:User {id: $user_id})-[:WATCHES]->(a:Asset)
        RETURN a.symbol AS symbol, a.name AS name, a.asset_type AS asset_type
        ORDER BY a.symbol ASC
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, user_id=user_id)
            return [dict(record) for record in result]

    def add_to_watchlist(self, user_id, symbol, name=None, asset_type="STOCK"):
        symbol = symbol.strip().upper()
        name = name.strip() if name else symbol
        query = """
        MATCH (u:User {id: $user_id})
        MERGE (a:Asset {symbol: $symbol})
          ON CREATE SET a.name = $name, a.asset_type = $asset_type, a.currency = 'INR'
        MERGE (u)-[:WATCHES]->(a)
        RETURN a.symbol AS symbol, a.name AS name, a.asset_type AS asset_type
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, user_id=user_id, symbol=symbol, name=name, asset_type=asset_type)
            record = result.single()
            return dict(record)

    def remove_from_watchlist(self, user_id, symbol):
        symbol = symbol.strip().upper()
        query = """
        MATCH (u:User {id: $user_id})-[r:WATCHES]->(a:Asset {symbol: $symbol})
        DELETE r
        RETURN count(r) AS removed_count
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, user_id=user_id, symbol=symbol)
            record = result.single()
            return {"removed": record["removed_count"] > 0}

    def close(self):
        self.driver.close()

