from __future__ import annotations

import datetime as dt
import pathlib
from uuid import uuid4

from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from bot.handlers.resume import ALLOWED_EXT, extract_text, process_resume
from bot.keyboards import POST_UPLOAD_KB, vacancy_inline_kb
from settings.config import setup
from vacancies import VACANCIES

router = Router()

MSG_FMT_UNSUPPORTED = (
    "❌ Этот формат не поддерживается. " "Пришлите файл DOC/DOCX, PDF или TXT."
)
MSG_MENU_HELP = "ℹ️ Воспользуйтесь меню, чтобы увидеть список доступных команд."
MSG_AFTER_UPLOAD = (
    "Спасибо! Мы свяжемся с вами после рассмотрения.\n"
    "Подпишитесь на @rakestep, чтобы не пропустить новости."
)


# /start
@router.message(CommandStart())
async def cmd_start(m: types.Message, state: FSMContext) -> None:
    await m.answer("Выберите вакансию:", reply_markup=types.ReplyKeyboardRemove())
    await m.answer("Актуальные вакансии:", reply_markup=vacancy_inline_kb())
    await state.clear()


# /info
@router.message(Command("info"))
async def cmd_info(m: types.Message) -> None:
    await m.answer(
        "1️⃣ /start – список вакансий\n"
        "2️⃣ Пришлите резюме (PDF/DOCX/TXT)\n"
        "3️⃣ Получите обратную связь и рейтинг\n"
        "После загрузки появятся кнопки:"
        " «👀 Посмотреть вакансии» и «📄 Моё резюме»."
    )


# reply-кнопка «Посмотреть вакансии»
@router.message(F.text == "👀 Посмотреть вакансии")
async def show_vacancies(m: types.Message) -> None:
    await m.answer("Актуальные вакансии:", reply_markup=vacancy_inline_kb())


# reply-кнопка «Моё резюме»
@router.message(F.text == "📄 Моё резюме")
async def send_my_resume(m: types.Message, state: FSMContext) -> None:
    file_id = (await state.get_data()).get("resume_file_id")
    await (
        m.answer_document(file_id)
        if file_id
        else m.answer("Вы ещё не отправляли резюме.")
    )


# выбор вакансии
@router.callback_query(F.data.startswith("vac|"))
async def choose_vacancy(cb: types.CallbackQuery, state: FSMContext) -> None:
    vacancy = cb.data.split("|", 1)[1]
    await state.update_data(vacancy=vacancy)
    await cb.message.edit_text(
        f"Вы выбрали <b>{vacancy}</b>\n" "Пришлите файл PDF, DOC/DOCX или TXT с резюме."
    )
    await cb.answer()


# обработка документов
@router.message(F.document)
async def handle_document(m: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    vacancy = data.get("vacancy")
    if not vacancy:
        return await m.answer("Сначала выберите вакансию через /start.")

    ext = pathlib.Path(m.document.file_name or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        return await m.answer(MSG_FMT_UNSUPPORTED)

    # сохранение файла
    ts = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    target = pathlib.Path(setup.data_dir) / f"{ts}_{uuid4().hex}{ext}"
    file_info = await m.bot.get_file(m.document.file_id)
    await m.bot.download_file(file_info.file_path, destination=target)

    resume_txt = extract_text(str(target))
    meta = await process_resume(
        file_path=str(target),
        resume_text=resume_txt,
        vacancy_name=vacancy,
        vacancy_text=VACANCIES[vacancy],
        user_id=m.from_user.id,
    )

    await state.update_data(resume_file_id=m.document.file_id)
    await m.answer(MSG_AFTER_UPLOAD, reply_markup=POST_UPLOAD_KB)

    caption = (
        f'{meta["tag"]} {meta["rating"]:.0f}% — <b>{vacancy}</b>\n'
        f'{meta["summary"]}\n'
        f'Советы: {meta["interview_tips"]}'
    )
    await m.bot.send_document(
        setup.summary_chat_id, m.document.file_id, caption=caption
    )


# прочие сообщения
@router.message()
async def catch_all(m: types.Message) -> None:
    await m.answer(MSG_MENU_HELP)
