import json
import os
import sys
from datetime import datetime, timedelta
import pandas as pd
from PIL import Image
from PIL.ExifTags import TAGS
from tinydb import Query, TinyDB

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def get_exif_coordinates(pil_image: Image.Image):
    """Extract GPS coordinates from image EXIF data if present."""
    if pil_image is None:
        return None
    try:
        exif = pil_image._getexif()
        if not exif:
            return None
        gps_info = {}
        for tag, value in exif.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_info = value
                break
        if not gps_info:
            return None

        def _convert_to_degrees(value):
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
            return d + (m / 60.0) + (s / 3600.0)

        lat = _convert_to_degrees(gps_info[2])
        if gps_info[1] == "S":
            lat = -lat
        lon = _convert_to_degrees(gps_info[4])
        if gps_info[3] == "W":
            lon = -lon
        return [round(lat, 5), round(lon, 5)]
    except Exception:
        return None


from src.preprocess import sanitize_string


class Storage:
    def __init__(self):
        self.backend = os.getenv("STORAGE_BACKEND", "tinydb").lower()
        if self.backend == "mongodb":
            import pymongo

            mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
            client = pymongo.MongoClient(mongo_uri)
            db = client["dumpwatch_db"]
            self.collection = db["reports"]
        else:
            os.makedirs(config.DATA_DIR, exist_ok=True)
            self._init_tinydb()

    def _init_tinydb(self):
        """Initialize or repair TinyDB instance."""
        try:
            if os.path.exists(config.TINYDB_PATH):
                with open(config.TINYDB_PATH, "r", encoding="utf-8") as f:
                    json.load(f)
        except Exception:
            # Corrupted DB file, remove it
            try:
                os.remove(config.TINYDB_PATH)
            except Exception:
                pass
        
        try:
            self.db = TinyDB(config.TINYDB_PATH)
            self.table = self.db.table("reports")
        except Exception:
            if os.path.exists(config.TINYDB_PATH):
                os.remove(config.TINYDB_PATH)
            self.db = TinyDB(config.TINYDB_PATH)
            self.table = self.db.table("reports")

    def insert_report(self, report_doc: dict):
        # Sanitize report string fields
        clean_doc = {}
        for k, v in report_doc.items():
            if isinstance(v, str):
                clean_doc[k] = sanitize_string(v)
            else:
                clean_doc[k] = v

        if self.backend == "mongodb":
            self.collection.insert_one(clean_doc.copy())
        else:
            try:
                self.table.insert(clean_doc)
            except Exception:
                self._init_tinydb()
                try:
                    self.table.insert(clean_doc)
                except Exception:
                    pass
        append_to_csv(clean_doc)

    def get_all(self) -> list:
        # Single source of truth: return records from reports.csv if available
        df = get_reports_df()
        if not df.empty:
            records = []
            for _, r in df.iterrows():
                d = r.to_dict()
                d["coordinates"] = [r["lat"], r["lon"]]
                records.append(d)
            return records

        if self.backend == "mongodb":
            return list(self.collection.find({}, {"_id": 0}))
        else:
            try:
                return self.table.all()
            except Exception:
                self._init_tinydb()
                return []

    def get_recent(self, days: int = 7) -> list:
        all_docs = self.get_all()
        cutoff = datetime.now() - timedelta(days=days)
        recent = []
        for d in all_docs:
            try:
                ts = datetime.strptime(str(d["timestamp"]), "%Y-%m-%d %H:%M:%S")
                if ts >= cutoff:
                    recent.append(d)
            except Exception:
                recent.append(d)
        return recent

    def update_status(self, report_id: str, status: str):
        if self.backend == "mongodb":
            self.collection.update_one({"report_id": report_id}, {"$set": {"status": status}})
        else:
            try:
                Report = Query()
                self.table.update({"status": status}, Report.report_id == report_id)
            except Exception:
                self._init_tinydb()

        # Sync to CSV
        csv_path = os.path.join(config.DATA_DIR, "reports.csv")
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                df.loc[df["report_id"] == report_id, "status"] = status
                df.to_csv(csv_path, index=False)
            except Exception:
                pass

    def count(self) -> int:
        csv_path = os.path.join(config.DATA_DIR, "reports.csv")
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                return len(df)
            except Exception:
                pass
        if self.backend == "mongodb":
            return self.collection.count_documents({})
        else:
            try:
                return len(self.table)
            except Exception:
                self._init_tinydb()
                return 0

    def clear(self):
        if self.backend == "mongodb":
            self.collection.delete_many({})
        else:
            try:
                self.table.truncate()
            except Exception:
                if os.path.exists(config.TINYDB_PATH):
                    try:
                        os.remove(config.TINYDB_PATH)
                    except Exception:
                        pass
                self._init_tinydb()

        csv_path = os.path.join(config.DATA_DIR, "reports.csv")
        if os.path.exists(csv_path):
            try:
                os.remove(csv_path)
            except Exception:
                pass


def get_waste_types() -> list:
    """Load waste types including custom saved types."""
    waste_path = os.path.join(config.DATA_DIR, "waste_types.json")
    types = list(config.WASTE_TYPES)
    if os.path.exists(waste_path):
        try:
            with open(waste_path, "r", encoding="utf-8") as f:
                custom_types = json.load(f)
                for ct in custom_types:
                    if ct not in types:
                        types.append(ct)
        except Exception:
            pass
    if "Others" not in types:
        types.append("Others")
    return types


def save_custom_waste_type(new_type: str):
    """Save a new custom waste type to waste_types.json."""
    if not new_type or new_type.strip() == "":
        return
    cleaned = new_type.strip()
    waste_path = os.path.join(config.DATA_DIR, "waste_types.json")
    existing = []
    if os.path.exists(waste_path):
        try:
            with open(waste_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []
    if cleaned not in existing and cleaned not in config.WASTE_TYPES:
        existing.append(cleaned)
        os.makedirs(config.DATA_DIR, exist_ok=True)
        with open(waste_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)


def get_reports_df() -> pd.DataFrame:
    """Read reports from data/reports.csv as single source of truth."""
    csv_path = os.path.join(config.DATA_DIR, "reports.csv")
    if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
        # Check if sample_reports.csv exists to initialize
        load_sample_csv()
    if os.path.exists(csv_path):
        try:
            return pd.read_csv(csv_path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def append_to_csv(report_doc: dict):
    """Append a report dictionary to data/reports.csv."""
    csv_path = os.path.join(config.DATA_DIR, "reports.csv")
    os.makedirs(config.DATA_DIR, exist_ok=True)

    coords = report_doc.get("coordinates", [config.DEFAULT_MAP_CENTER[0], config.DEFAULT_MAP_CENTER[1]])
    row = {
        "report_id": sanitize_string(report_doc.get("report_id", "")),
        "timestamp": sanitize_string(report_doc.get("timestamp", "")),
        "source": sanitize_string(report_doc.get("source", "citizen")),
        "raw_text": sanitize_string(report_doc.get("raw_text", "")),
        "waste_type": sanitize_string(report_doc.get("waste_type", "household garbage")),
        "severity": report_doc.get("severity", 3),
        "lat": coords[0] if isinstance(coords, (list, tuple)) and len(coords) > 0 else config.DEFAULT_MAP_CENTER[0],
        "lon": coords[1] if isinstance(coords, (list, tuple)) and len(coords) > 1 else config.DEFAULT_MAP_CENTER[1],
        "location_text": sanitize_string(report_doc.get("location_text", "Thane")),
        "has_image": report_doc.get("has_image", False),
        "image_path": sanitize_string(report_doc.get("image_path", "")),
        "status": sanitize_string(report_doc.get("status", "Pending")),
        "duplicate_of": sanitize_string(report_doc.get("duplicate_of", "") if report_doc.get("duplicate_of") else ""),
    }

    file_exists = os.path.exists(csv_path) and os.path.getsize(csv_path) > 0
    df_row = pd.DataFrame([row])
    df_row.to_csv(csv_path, mode="a", index=False, header=not file_exists)


def load_sample_csv():
    """Seed data/reports.csv and DB from sample data if reports.csv is missing."""
    csv_path = os.path.join(config.DATA_DIR, "reports.csv")
    if os.path.exists(csv_path) and os.path.getsize(csv_path) > 100:
        return

    sample_path = config.SAMPLE_CSV_PATH
    if not os.path.exists(sample_path):
        from scripts.generate_data import generate_synthetic_reports
        generate_synthetic_reports()

    df_sample = pd.read_csv(sample_path)
    
    # Transform sample df to match reports.csv schema
    formatted_rows = []
    for _, row in df_sample.iterrows():
        is_dumping = row.get("is_dumping", True)
        status = "Pending" if is_dumping else "Rejected"
        formatted_rows.append({
            "report_id": row.get("report_id", ""),
            "timestamp": row.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "source": row.get("source", "citizen"),
            "raw_text": row.get("raw_text", ""),
            "waste_type": row.get("waste_type", "household garbage"),
            "severity": row.get("severity", 3),
            "lat": row.get("lat", config.DEFAULT_MAP_CENTER[0]),
            "lon": row.get("lon", config.DEFAULT_MAP_CENTER[1]),
            "location_text": row.get("locality", "Thane"),
            "has_image": row.get("has_image", False),
            "image_path": "",
            "status": status,
            "duplicate_of": "",
        })
    
    df_out = pd.DataFrame(formatted_rows)
    os.makedirs(config.DATA_DIR, exist_ok=True)
    df_out.to_csv(csv_path, index=False)


# --- EMPLOYEE DATABASE STORAGE ---
def get_employees_path():
    return os.path.join(config.DATA_DIR, "employees.json")


def get_all_employees() -> list:
    """Retrieve list of registered employees."""
    path = get_employees_path()
    if not os.path.exists(path):
        # Default initial admin employee account
        default_admin = [{
            "employee_id": "EMP1001",
            "name": "System Administrator",
            "password": "admin",
            "role": "Administrator",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }]
        os.makedirs(config.DATA_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_admin, f, indent=2)
        return default_admin
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def register_employee(emp_id: str, name: str, password: str, role: str = "Backoffice Officer") -> tuple[bool, str]:
    """Register a new admin/employee account."""
    emp_id = emp_id.strip().upper()
    name = name.strip()
    if not emp_id or not name or not password:
        return False, "All fields (Employee ID, Name, Password) are required."
    
    employees = get_all_employees()
    for emp in employees:
        if emp["employee_id"] == emp_id:
            return False, f"Employee ID '{emp_id}' is already registered."

    new_emp = {
        "employee_id": emp_id,
        "name": name,
        "password": password,
        "role": role,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    employees.append(new_emp)
    
    try:
        os.makedirs(config.DATA_DIR, exist_ok=True)
        with open(get_employees_path(), "w", encoding="utf-8") as f:
            json.dump(employees, f, indent=2)
        return True, "Employee account registered successfully!"
    except Exception as e:
        return False, f"Failed to save employee data: {e}"


def authenticate_employee(emp_id: str, password: str) -> tuple[bool, dict]:
    """Validate employee login credentials."""
    emp_id = emp_id.strip().upper()
    employees = get_all_employees()
    for emp in employees:
        if emp["employee_id"] == emp_id and emp["password"] == password:
            return True, emp
    return False, {}

