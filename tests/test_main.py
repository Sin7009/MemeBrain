import os

from src.main import SingleInstanceLock


def test_single_instance_lock_acquire_and_release(tmp_path):
    lock_path = tmp_path / "memebrain_test.lock"
    lock = SingleInstanceLock(str(lock_path))

    assert lock.acquire() is True
    assert lock_path.exists()

    lock.release()
    assert not lock_path.exists()


def test_single_instance_lock_detects_running_pid(tmp_path):
    lock_path = tmp_path / "memebrain_test.lock"

    # Пишем текущий PID как будто уже есть активный инстанс
    lock_path.write_text(str(os.getpid()), encoding="utf-8")

    lock = SingleInstanceLock(str(lock_path))
    assert lock.acquire() is False


def test_single_instance_lock_recovers_stale_lock(tmp_path):
    lock_path = tmp_path / "memebrain_test.lock"

    # PID, который почти наверняка не существует
    lock_path.write_text("999999", encoding="utf-8")

    lock = SingleInstanceLock(str(lock_path))
    assert lock.acquire() is True
    assert lock_path.exists()

    # Файл должен содержать уже текущий PID
    assert lock_path.read_text(encoding="utf-8").strip() == str(os.getpid())

    lock.release()
