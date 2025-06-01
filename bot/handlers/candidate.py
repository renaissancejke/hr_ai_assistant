import os, datetime, pathlib
from uuid import uuid4

from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from settings.config import setup
from vacancies import VACANCIES
from bot.keyboards import (
    MAIN_REPLY_KB,
    post_upload_kb,
    vacancy_inline_kb,
)
from bot.handlers.resume import process_resume, extract_text

router = Router()


@router.message(CommandStart())
async def cmd_start(msg: types.Message, state: FSMContext) -> None:

    await msg.answer(
        "Привет! Нажмите кнопку <b>«Посмотреть вакансии»</b> "
        "или выберите вакансию из списка:",
        reply_markup=MAIN_REPLY_KB,
    )
    await msg.answer(
        "Актуальные вакансии:",
        reply_markup=vacancy_inline_kb(),
    )
    await state.clear()


@router.message(Command("info"))
async def cmd_info(msg: types.Message) -> None:

    text = (
        "<b>🤖 HR-Assistant Bot</b>\n\n"
        "Бот принимает ваше резюме и автоматически сравнивает его "
        "с требованиями открытых вакансий.\n\n"
        "👉 <b>Как пользоваться</b>\n"
        "1️⃣ Нажмите «👀 Посмотреть вакансии» или выполните /start\n"
        "2️⃣ Выберите вакансию\n"
        "3️⃣ Отправьте PDF, DOC/DOCX или TXT с резюме\n"
        "4️⃣ Бот рассчитает рейтинг и передаст отчёт HR-команде\n\n"
        "После загрузки появится кнопка «📄 Моё резюме» — "
        "она всегда покажет последний отправленный файл."
    )
    await msg.answer(text)


@router.message(F.text == "👀 Посмотреть вакансии")
async def show_vacancies(msg: types.Message, state: FSMContext) -> None:

    await msg.answer(
        "Актуальные вакансии:",
        reply_markup=vacancy_inline_kb(),
    )


@router.message(F.text == "📄 Моё резюме")
async def send_my_resume(msg: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    file_id = data.get("resume_file_id")
    if file_id:
        await msg.answer_document(file_id)
    else:
        await msg.answer("Вы ещё не отправляли резюме.")


@router.callback_query(F.data.startswith("vac|"))
async def choose_vacancy(cb: types.CallbackQuery, state: FSMContext) -> None:
    vacancy = cb.data.split("|", 1)[1]
    await state.update_data(vacancy=vacancy)
    await cb.message.edit_text(
        f"Вы выбрали <b>{vacancy}</b>.\n"
        f"Пришлите PDF, DOC/DOCX или TXT файл с резюме."
    )
    await cb.answer()


@router.message(F.document)
async def handle_document(msg: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    if "vacancy" not in data:
        await msg.answer("Сначала выберите вакансию (кнопка или /start).")
        return

    filename = (msg.document.file_name or "").lower()
    ext = pathlib.Path(filename).suffix.lstrip(".")
    ALLOWED = {"txt", "pdf", "doc", "docx"}
    if ext not in ALLOWED:
        await msg.answer("❌ Поддерживаются только PDF, DOC, DOCX и TXT.")
        return

    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    save_name = f"{ts}_{uuid4().hex}.{ext}"
    path = os.path.join(setup.data_dir, save_name)

    file_info = await msg.bot.get_file(msg.document.file_id)
    await msg.bot.download_file(file_info.file_path, destination=path)

    resume_txt = extract_text(path)

    vacancy_name = data["vacancy"]
    vacancy_text = VACANCIES[vacancy_name]
    meta = await process_resume(
        file_path=path,
        resume_text=resume_txt,
        vacancy_name=vacancy_name,
        vacancy_text=vacancy_text,
        user_id=msg.from_user.id,
    )

    await state.update_data(resume_file_id=msg.document.file_id)

    await msg.answer(
        "Спасибо! Ответим в течение недели.\n"
        "Подпишитесь на @rakestep, чтобы не пропустить новости.",
        reply_markup=post_upload_kb(),
    )

    caption = (
        f'{meta["tag"]} {meta["rating"]:.0f}% — <b>{vacancy_name}</b>\n'
        f'{meta["summary"]}\n'
        f'Советы: {meta["interview_tips"]}'
    )
    await msg.bot.send_document(
        setup.summary_chat_id,
        msg.document.file_id,
        caption=caption,
    )
