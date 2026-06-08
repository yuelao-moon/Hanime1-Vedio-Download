from __future__ import annotations

from python_backend.app.scraper import parse_comment_context


def test_parse_comment_context_extracts_create_comment_form_token_and_user():
    html = """
    <div id="comment-create-form-wrapper">
      <form id="comment-create-form" action="https://hanime1.me/createComment" method="POST">
        <input type="hidden" name="_token" value="comment-csrf">
        <input name="comment-user-id" type="hidden" value="664762">
        <input name="comment-type" type="hidden" value="video">
        <input name="comment-foreign-id" type="hidden" value="406536">
        <img src="https://img.test/avatar.jpg">
      </form>
    </div>
    <div class="comment-wrapper">
      <button class="report-comment-btn" data-reportable-id="403817"></button>
      <div class="comment-index-text">Tester</div>
      <div class="comment-index-text">hello</div>
    </div>
    """

    result = parse_comment_context(html, "406536")

    assert result["csrfToken"] == "comment-csrf"
    assert result["currentUserId"] == "664762"
    assert result["avatarUrl"] == "https://img.test/avatar.jpg"
    assert result["videoId"] == "406536"
    assert result["comments"] == []


def test_parse_comment_context_extracts_comment_like_state():
    html = """
    <div class="report-btn-wrapper">
      <button class="report-btn" data-reportable-id="406416"></button>
      <div class="comment-index-text">yuelao <span>40秒前</span></div>
      <div class="comment-index-text">都过来换电</div>
    </div>
    <div>
      <form class="comment-like-form" action="https://hanime1.me/commentLike" method="POST">
        <input type="hidden" name="_token" value="comment-csrf">
        <input type="hidden" id="foreign_type" name="foreign_type" value="comment">
        <input type="hidden" id="foreign_id" name="foreign_id" value="406416">
        <input type="hidden" id="is_positive" name="is_positive" value="">
        <button class="no-button-style comment-like-btn">
          <input name="comment-like-user-id" type="hidden" value="664762">
          <input name="like-comment-status" type="hidden" value="1">
          <input name="comment-likes-count" type="hidden" value="1">
          <input name="comment-likes-sum" type="hidden" value="1">
          <input name="unlike-comment-status" type="hidden" value="0">
        </button>
      </form>
    </div>
    """

    result = parse_comment_context(html, "406536")

    assert result["comments"][0]["commentId"] == "406416"
    assert result["comments"][0]["likeCount"] == 1
    assert result["comments"][0]["likeStatus"] == "1"
    assert result["comments"][0]["unlikeStatus"] == "0"
    assert result["comments"][0]["likeUserId"] == "664762"
    assert result["comments"][0]["foreignType"] == "comment"
    assert result["comments"][0]["foreignId"] == "406416"
