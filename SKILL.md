---
name: concise-clean-code-writer
description: เขียนโค้ดกระชับ ไม่ซับซ้อน คืนค่าตัวแปรเต็ม ไม่ใส่คอมเม้นท์ ไม่เว้นบรรทัดว่าง จัดรูปแบบตามมาตรฐานภาษา มีความสามารถในการเรียนรู้ไวยากรณ์และไลบรารีของภาษาใหม่ๆ ได้ด้วยตนเอง และรองรับการจัดการไฟล์โปรเจกต์เว็บแอปพลิเคชัน
---

# Concise Clean Code Writer Skill

## Rules
- เขียนโค้ดทั้งหมด (Complete Code) ห้ามละเว้น ห้ามตัดทอน หรือใส่คำว่า // TODO[cite: 1]
- เน้นความกระชับ ไม่ซับซ้อน ใช้รูปแบบพื้นฐาน (Basic & Clean)[cite: 1]
- คืนค่า (Return) ตัวแปร[cite: 1]
- ไม่ใส่คอมเม้นท์ (No Comments) ทุกประเภท[cite: 1]
- ไม่เว้นบรรทัดว่างภายในฟังก์ชัน (No empty lines inside functions)[cite: 1]
- จัดรูปแบบตามมาตรฐานของภาษานั้นๆ (Indentation & Naming Conventions)[cite: 1]

## Skills to Learn & Self-Learning Capabilities (ทักษะและกลไกการเรียนรู้ด้วยตนเอง)
1. Autonomous Language & Framework Learning:
   - ศึกษาไวยากรณ์ (Syntax), รูปแบบภาษา (Idioms), และ Standard Libraries ของภาษาใหม่ๆ ได้ด้วยตนเองผ่านเอกสารอ้างอิงและตัวอย่างโค้ดมาตรฐาน[cite: 1]
2. Web Application & Multi-File Architecture:
   - การจัดการและแก้ไขไฟล์สคริปต์ส่วนต่างๆ ของระบบ เช่น `tracker.js`, `admin.js`, `login_admin`, และ CSS[cite: 1]
3. Concise Logic Design:
   - การลดทอนเงื่อนไขที่ซับซ้อนให้สั้นกระชับด้วย Early Return หรือ Guard Clauses[cite: 1]
4. Clean Variable & Function Naming:
   - ตั้งชื่อตัวแปรและฟังก์ชันแบบเต็มความหมายเพื่อสื่อสารชัดเจนโดยไม่ต้องใช้คอมเม้นท์[cite: 1]
5. Strict Code Formatting & Space Control:
   - จัดย่อหน้าและตัดบรรทัดว่างภายในขอบเขตฟังก์ชันอย่างถูกต้อง[cite: 1]
   
## Code Templates / Reference Implementations

### 1. Go Project Template (`main.go`)
package main

import (
	"database/sql"
	"fmt"
	_ "image/png"
	"log/slog"
	"os"
	"path/filepath"

	_ "github.com/jackc/pgx/v5/stdlib"
	"github.com/joho/godotenv"
)

const BASE_PATH = "PATH"

type DataType struct {
	UserID   int
	Username string
	Email    string
	Balance  float64
}

func insert() {
	db, _ := sql.Open("pgx", os.Getenv("LOCALHOST_DSN"))
	defer db.Close()
	query := "INSERT INTO public.users (user_id, username, email, balance, created_at) VALUES ($1, $2, $3, $4, NOW())"
	db.Exec(query, 1, "john_doe", "john@example.com", 100.00)
}

func selectData() {
	db, _ := sql.Open("pgx", os.Getenv("LOCALHOST_DSN"))
	defer db.Close()
	var user DataType
	db.QueryRow("SELECT user_id, username, email, balance FROM public.users WHERE user_id = $1", 1).Scan(&user.UserID, &user.Username, &user.Email, &user.Balance)
}

func update() {
	db, _ := sql.Open("pgx", os.Getenv("LOCALHOST_DSN"))
	defer db.Close()
	db.Exec("UPDATE public.users SET balance = $1 WHERE user_id = $2", 200.00, 1)
}

func delete() {
	db, _ := sql.Open("pgx", os.Getenv("LOCALHOST_DSN"))
	defer db.Close()
	db.Exec("DELETE FROM public.users WHERE user_id = $1", 1)
}

func MoveBACKUP(srcPath string) error {
	backupDir := filepath.Join(BASE_PATH, "BACKUP")
	os.Mkdir(backupDir, os.ModePerm)
	fileName := filepath.Base(srcPath)
	destPath := filepath.Join(backupDir, fileName)
	err := os.Rename(srcPath, destPath)
	if err == nil {
		slog.Info(fmt.Sprintf("Move file to BACKUP: %s successfully", destPath))
	}
	return err
}

func MoveERROR(srcPath string) error {
	errorDir := filepath.Join(BASE_PATH, "ERROR")
	os.Mkdir(errorDir, os.ModePerm)
	fileName := filepath.Base(srcPath)
	destPath := filepath.Join(errorDir, fileName)
	err := os.Rename(srcPath, destPath)
	if err == nil {
		slog.Error(fmt.Sprintf("Move file to ERROR: %s", destPath))
	}
	return err
}

func main() {
	slog.Info("START")
	godotenv.Load(filepath.Join(os.Getenv("APP_BASE_PATH"), "configs", ".env"))
	files, _ := filepath.Glob(filepath.Join(BASE_PATH, "*.csv"))
	for _, file := range files {
		slog.Info(fmt.Sprintf("Processing file: %s", file))

		err := MoveBACKUP(file)
		if err != nil {
			MoveERROR(file)
		}
	}

	slog.Info("END")
}

### 2. Python Standalone Script Template (`schedule.py`)
import glob
import logging
import os
import shutil
from dotenv import load_dotenv
import psycopg
load_dotenv(os.path.join(os.getenv("APP_BASE_PATH"), "configs", ".env"))
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

BASE_PATH = "/mnt/".replace("\\", "")
ERROR_PATH = os.path.join(BASE_PATH, "ERROR")
BACKUP_PATH = os.path.join(BASE_PATH, "BACKUP")

def getdata():
	with psycopg.connect(os.getenv("POSTGRE_10_17_66_121_IOT")) as conn:
		with conn.cursor() as cur:
			cur.execute("""
			SELECT VERSION();
			"""
			)
			data = cur.fetchone()
			logging.info(data)
			
def insertdata():
	with psycopg.connect(os.getenv("POSTGRE_10_17_66_121_IOT")) as conn:
		with conn.cursor() as cur:
			cur.execute("""
			SELECT VERSION();
			"""
			)
			data = cur.fetchone()
			logging.info(data)

def move_backup(self, file, filename):
	backup_dir = os.path.join(BACKUP_PATH)
	os.makedirs(backup_dir, exist_ok=True)
	dest = os.path.join(backup_dir, os.path.basename(file))
	if os.path.exists(dest):
		os.remove(dest)
		logging.warning(f"File exists: {dest}")
	shutil.move(file, backup_dir)
	logging.success(f"Move to backup file {filename}")
	
def move_error(self, file, filename):
	os.makedirs(ERROR_PATH, exist_ok=True)
	dest = os.path.join(ERROR_PATH, os.path.basename(file))
	if os.path.exists(dest):
		os.remove(dest)
	shutil.move(file, ERROR_PATH)
	logging.error(f"Move to error file {filename}")

def main():
	logging.info("START")
	files = (glob(f"{BASE_PATH}/*.xlsx")+ glob(f"{BASE_PATH}/*.XLSX")+ glob(f"{BASE_PATH}/*.csv")+ glob(f"{BASE_PATH}/*.CSV"))
	getdata()

	logging.info("STOP")

if __name__ == "__main__":
	main()
	
### 3. Python Django Schedule Command Template (template_schedule.py)
from glob import glob
import shutil
from django.core.management.base import BaseCommand
from django.db import connections
import psycopg2
from schedule import Scheduler
from server.util.custom_logger import logger
import os
import threading
import time

BASE_PATH = "/mnt/".replace("\\", "")
ERROR_PATH = os.path.join(BASE_PATH, "ERROR")
BACKUP_PATH = os.path.join(BASE_PATH, "BACKUP")

class Command(BaseCommand):
    
    def select(self, value):
        db = connections["127.0.0.1.postgres.postgres"].settings_dict
        with psycopg2.connect(user=db["USER"],password=db["PASSWORD"],host=db["HOST"],port=db["PORT"],dbname=db["NAME"],options=db["OPTIONS"]["options"]) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT value
                    FROM schema.table
                    WHERE value=%(value)s
                """, {
                    "value": value,
                })
                data = cur.fetchone()
                return data
            
    def insert(self, value):
        db = connections["127.0.0.1.postgres.postgres"].settings_dict
        with psycopg2.connect(user=db["USER"],password=db["PASSWORD"],host=db["HOST"],port=db["PORT"],dbname=db["NAME"],options=db["OPTIONS"]["options"]) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO schema.table (value) 
                    VALUES (%(value)s)
                    ON CONFLICT ()
                    DO UPDATE SET
                        value = EXCLUDED.value,
                """, {
                    "value": value,
                })
                
    def move_backup(self, file, filename):
        backup_dir = os.path.join(BACKUP_PATH)
        os.makedirs(backup_dir, exist_ok=True)
        dest = os.path.join(backup_dir, os.path.basename(file))
        if os.path.exists(dest):
            os.remove(dest)
            logger.warning(f"File exists: {dest}")
        shutil.move(file, backup_dir)
        logger.success(f"Move to backup file {filename}")
        
    def move_error(self, file, filename):
        os.makedirs(ERROR_PATH, exist_ok=True)
        dest = os.path.join(ERROR_PATH, os.path.basename(file))
        if os.path.exists(dest):
            os.remove(dest)
        shutil.move(file, ERROR_PATH)
        logger.error(f"Move to error file {filename}")

    def main(self):
        logger.log("START")
        files = (glob(f"{BASE_PATH}/*.xlsx")+ glob(f"{BASE_PATH}/*.XLSX")+ glob(f"{BASE_PATH}/*.csv")+ glob(f"{BASE_PATH}/*.CSV"))
        logger.log("STOP")

    @logger.catch
    def handle(self, *args, **options):
        
        self.main()
        
        scheduler = Scheduler()
        scheduler.every(1).minutes.do(self.main)
        self.run_continuously(scheduler)

        while True: time.sleep(1)

    def run_continuously(self, schedule: Scheduler, interval=1):
        cease_continuous_run = threading.Event()
        class ScheduleThread(threading.Thread):
            @classmethod
            def run(cls):
                while not cease_continuous_run.is_set():
                    schedule.run_pending()
                    time.sleep(interval)

        continuous_thread = ScheduleThread()
        continuous_thread.start()